"""The read routes the screens render, and the two PDF exports.

Every payload here carries the synthetic-data notice (US-037, AC-119/121) and
every page of every export ends with the same sentence (AC-120), because the
whole product runs on a synthetic cohort and nothing it shows may be mistaken
for a real patient's record.

The reads themselves are deliberately thin: they answer from the loaded event
store, oldest first, with no paging (behaviour rules), and the clinical
scoring each screen eventually shows belongs to its own ticket.
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Event, Note, Patient, Persona, User
from app.notice import with_notice
from app.pdf import render_pdf
from app.sessions import CurrentUser, require_staff

router = APIRouter(tags=["data"])

Db = Annotated[Session, Depends(get_db)]
Staff = Annotated[User, Depends(require_staff)]


def _iso(value: Any) -> str | None:
    return None if value is None else value.isoformat()


def _history_lines(items: list[dict[str, Any]]) -> list[str]:
    """One line per timeline item, for a PDF page; never an empty page."""
    return [f"{item['item_time']} {item['display'] or ''}" for item in items] or [
        "No history to show."
    ]


def _patients(db: Session) -> list[Patient]:
    return list(db.execute(select(Patient).order_by(Patient.display_name)).scalars())


def _my_patient(db: Session, user: User) -> Patient | None:
    """The patient the signed-in account looks at: their own, or the first
    patient of the cohort for a clinician or admin previewing the screen."""
    if user.patient_id:
        return db.get(Patient, user.patient_id)
    cohort = _patients(db)
    return cohort[0] if cohort else None


def _timeline_items(db: Session, patient: Patient | None) -> list[dict[str, Any]]:
    if patient is None:
        return []
    rows = list(
        db.execute(
            select(Event).where(Event.patient_id == patient.id).order_by(Event.event_time)
        ).scalars()
    )
    refs = {row.source_ref for row in rows if row.source_ref}
    notes: dict[str, Note] = {}
    if refs:
        notes = {
            note.source_ref: note
            for note in db.execute(
                select(Note).where(Note.patient_id == patient.id, Note.source_ref.in_(refs))
            ).scalars()
        }
    items: list[dict[str, Any]] = []
    for row in rows:
        # The note `source_ref` points at, when there is one: provenance is
        # followed on the read, so a screen shows the text behind an item
        # rather than asserting it unsourced (AC-006).
        note = notes.get(row.source_ref or "")
        items.append(
            {
                "id": row.id,
                "patient_id": row.patient_id,
                "event_id": row.source_event_id,
                "source_event_id": row.source_event_id,
                "item_time": _iso(row.event_time),
                "event_time": _iso(row.event_time),
                "event_type": row.event_type,
                "code_system": row.code_system,
                "code": row.code,
                "display": row.display,
                "value": row.value,
                "unit": row.unit,
                "provider_org": row.provider_org,
                "provider_specialty": row.provider_specialty,
                "source_type": row.source_type,
                "source_ref": row.source_ref,
                "encounter_ref": row.encounter_ref,
                "confidence": row.confidence,
                "dataset_version": row.dataset_version,
                "note_text": note.text if note else None,
                "note_type": note.note_type if note else None,
                "note_time": _iso(note.note_time) if note else None,
            }
        )
    return items


@router.get("/api/worklist")
def worklist(user: Staff, db: Db) -> dict[str, Any]:
    """Every patient in the loaded cohort, with the notice (no paging)."""
    return with_notice(
        {
            "items": [
                {
                    "patient_id": patient.id,
                    "display_name": patient.display_name,
                    "dataset_patient_id": patient.dataset_patient_id,
                }
                for patient in _patients(db)
            ]
        }
    )


@router.get("/api/patients/me/timeline")
def my_timeline(user: CurrentUser, db: Db) -> dict[str, Any]:
    patient = _my_patient(db, user)
    return with_notice(
        {
            "patient_id": patient.id if patient else None,
            "items": _timeline_items(db, patient),
        }
    )


@router.get("/api/patients/me/updates")
def my_updates(user: CurrentUser, db: Db) -> dict[str, Any]:
    patient = _my_patient(db, user)
    items = _timeline_items(db, patient)
    return with_notice({"patient_id": patient.id if patient else None, "items": items[-5:]})


def _visit_prep(db: Session, patient: Patient | None) -> dict[str, Any]:
    items = _timeline_items(db, patient)
    return {
        "patient_id": patient.id if patient else None,
        "display_name": patient.display_name if patient else None,
        "items": items,
        "questions": [
            "How long has your back pain lasted?",
            "Is the pain worse after rest and better with movement?",
        ],
    }


@router.get("/api/patients/me/visit-prep")
def my_visit_prep(user: CurrentUser, db: Db) -> dict[str, Any]:
    return with_notice(_visit_prep(db, _my_patient(db, user)))


@router.get("/api/patients/me/visit-prep.pdf")
def my_visit_prep_pdf(user: CurrentUser, db: Db) -> Response:
    sheet = _visit_prep(db, _my_patient(db, user))
    first = [
        "Visit prep sheet",
        f"Patient: {sheet['display_name'] or 'unassigned'}",
        "",
        *sheet["questions"],
    ]
    return Response(
        content=render_pdf([first, _history_lines(sheet["items"])]),
        media_type="application/pdf",
    )


def _persona_bundle(db: Session, persona: Persona, view: str) -> dict[str, Any]:
    patient = db.get(Patient, persona.patient_id)
    return {
        "persona_key": persona.persona_key,
        "name": persona.name,
        "view": view,
        "patient_id": persona.patient_id,
        "display_name": patient.display_name if patient else None,
        "items": _timeline_items(db, patient),
    }


@router.get("/api/demo/personas")
def demo_personas(user: CurrentUser, db: Db) -> dict[str, Any]:
    rows = db.execute(select(Persona).order_by(Persona.persona_key)).scalars()
    return with_notice(
        {
            "personas": [
                {
                    "persona_key": row.persona_key,
                    "name": row.name,
                    "one_line_description": row.one_line_description,
                    "patient_id": row.patient_id,
                }
                for row in rows
            ]
        }
    )


class OpenPersona(BaseModel):
    view: str = "clinician"


def _persona_or_404(db: Session, persona_key: str) -> Persona:
    persona = (
        db.execute(select(Persona).where(Persona.persona_key == persona_key)).scalars().first()
    )
    if persona is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"no persona {persona_key}"
        )
    return persona


@router.post("/api/demo/personas/{persona_key}/open")
def open_persona(persona_key: str, body: OpenPersona, user: CurrentUser, db: Db) -> dict[str, Any]:
    persona = _persona_or_404(db, persona_key)
    return with_notice({"bundle": _persona_bundle(db, persona, body.view)})


@router.get("/api/demo/personas/{persona_key}/replay")
def persona_replay(persona_key: str, user: CurrentUser, db: Db) -> dict[str, Any]:
    persona = _persona_or_404(db, persona_key)
    bundle = _persona_bundle(db, persona, "replay")
    return with_notice(
        {
            "persona_key": persona.persona_key,
            "patient_id": persona.patient_id,
            "tracks": {"real_world": bundle["items"], "copilot": bundle["items"]},
        }
    )


@router.get("/api/cases/{patient_id}/timeline")
def case_timeline(patient_id: str, user: Staff, db: Db) -> dict[str, Any]:
    """One patient's stored events, each with its provenance and note text."""
    patient = db.get(Patient, patient_id)
    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"no patient {patient_id}"
        )
    return with_notice({"patient_id": patient.id, "items": _timeline_items(db, patient)})


@router.get("/api/evaluation/runs/latest")
def latest_evaluation(user: Staff, db: Db) -> dict[str, Any]:
    """The latest evaluation run. Until the evaluation job exists there is none,
    and the report says so -- with the notice, because its numbers come from
    the same synthetic cohort."""
    return with_notice({"run": None, "metrics": [], "cohort": "synthetic"})


@router.get("/api/cases/{patient_id}/referral-packet.pdf")
def referral_packet_pdf(patient_id: str, user: Staff, db: Db) -> Response:
    patient = db.get(Patient, patient_id)
    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"no patient {patient_id}"
        )
    pages = [
        [
            "Referral packet",
            f"Patient: {patient.display_name}",
            f"Dataset id: {patient.dataset_patient_id}",
        ],
        _history_lines(_timeline_items(db, patient)),
    ]
    return Response(content=render_pdf(pages), media_type="application/pdf")
