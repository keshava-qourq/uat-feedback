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

from datetime import UTC, datetime
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dedup import group_rows, merge_items
from app.engine.inputs import cutoff_date, is_pre_cutoff
from app.invites import worklist_invite_status
from app.models import Decision, Event, IntakeAnswer, Note, Patient, Persona, User
from app.notice import with_notice
from app.pack import get_active_pack
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
    """One patient's items, oldest first, with nothing dated on or after their
    evaluation cutoff (NFR-013, AC-028). The undated family-history row is the
    one exception; a patient with no cutoff recorded is not filtered at all."""
    if patient is None:
        return []
    cutoff = cutoff_date(db, patient.id)
    rows = list(
        db.execute(
            select(Event).where(Event.patient_id == patient.id).order_by(Event.event_time)
        ).scalars()
    )
    rows = [row for row in rows if is_pre_cutoff(row.event_time, cutoff, row.event_type)]
    # One real encounter can arrive as an EHR row and the claim it generated:
    # the same deterministic rule that persists `encounter_group_id` decides
    # here which rows belong together, so the read is right whether or not the
    # backfill has run (US-004-1).
    group_keys: dict[str, str] = {}
    for index, group in enumerate(group_rows(rows)):
        key = next(
            (member.encounter_group_id for member in group if member.encounter_group_id),
            f"group-{index}",
        )
        for member in group:
            group_keys[member.id] = key
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
                "encounter_group_id": group_keys.get(row.id) or row.encounter_group_id,
                "confidence": row.confidence,
                "dataset_version": row.dataset_version,
                "note_text": note.text if note else None,
                "note_type": note.note_type if note else None,
                "note_time": _iso(note.note_time) if note else None,
            }
        )
    # One entry per merged encounter, carrying its sources and the source rows
    # behind it; still ascending, oldest first (AC-011).
    return merge_items(items)


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
                    # AC-085: none until an invite is issued, then not_yet_opened,
                    # opened once the link is fetched, intake_completed after intake.
                    "invite_status": worklist_invite_status(db, patient.id),
                }
                for patient in _patients(db)
            ]
        }
    )


class DecisionBody(BaseModel):
    """What a clinician records on a case. The acting account is never in here."""

    decision: Literal["agree", "disagree", "need_more_info"]
    reason: str | None = None
    tier_at_time: str | None = None


@router.post("/api/cases/{patient_id}/decisions", status_code=status.HTTP_201_CREATED)
def record_decision(patient_id: str, body: DecisionBody, user: Staff, db: Db) -> dict[str, Any]:
    """AC-100: the decision stores the acting user_id from the verified session."""
    patient = db.get(Patient, patient_id)
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    previous = (
        db.execute(
            select(Decision)
            .where(Decision.patient_id == patient_id, Decision.superseded_by.is_(None))
            .order_by(Decision.created_at.desc())
        )
        .scalars()
        .first()
    )
    row = Decision(
        patient_id=patient_id,
        clinician_id=user.id,
        decision=body.decision,
        reason=body.reason,
        tier_at_time=body.tier_at_time,
    )
    db.add(row)
    db.flush()
    if previous is not None:
        previous.superseded_by = row.id
    db.commit()
    return {
        "decision_id": row.id,
        "clinician_id": row.clinician_id,
        "decision": row.decision,
        "created_at": _iso(row.created_at),
        "supersedes": previous.id if previous is not None else None,
    }


@router.get("/api/patients/me/timeline")
def my_timeline(user: CurrentUser, db: Db) -> dict[str, Any]:
    patient = _my_patient(db, user)
    return with_notice(
        {
            "patient_id": patient.id if patient else None,
            "items": _timeline_items(db, patient),
        }
    )


#: The question the intake asks when no condition pack is active: the pack owns
#: every condition-specific question key (NFR-019), and with no pack the intake
#: still has to be completable.
GENERIC_INTAKE_KEYS = ["general_history"]


def _intake_questions() -> list[dict[str, str]]:
    """The intake's questions: the active pack's keys, else the generic one."""
    pack = get_active_pack()
    keys: list[str] = []
    if pack is not None:
        for signal in pack.signals().values():
            for key in (signal or {}).get("intake_keys") or []:
                if key not in keys:
                    keys.append(key)
    return [{"key": key} for key in (keys or GENERIC_INTAKE_KEYS)]


def _answered_keys(db: Session, patient_id: str) -> set[str]:
    return set(
        db.execute(
            select(IntakeAnswer.question_key).where(IntakeAnswer.patient_id == patient_id)
        ).scalars()
    )


@router.get("/api/patients/me/intake")
def my_intake(user: CurrentUser, db: Db) -> dict[str, Any]:
    """AC-085: what the invited patient still has to answer."""
    patient = _my_patient(db, user)
    questions = _intake_questions()
    answered = _answered_keys(db, patient.id) if patient else set()
    pending = [question for question in questions if question["key"] not in answered]
    return with_notice(
        {
            "patient_id": patient.id if patient else None,
            "questions": questions,
            "next_question": pending[0] if pending else None,
            "complete": not pending,
        }
    )


class IntakeAnswerBody(BaseModel):
    question_key: str
    answer_value: Any = None


@router.post("/api/patients/me/intake/answers")
def record_intake_answer(body: IntakeAnswerBody, user: CurrentUser, db: Db) -> dict[str, Any]:
    """Store one intake answer; the last one marks the intake complete (AC-085)."""
    patient = _my_patient(db, user)
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    keys = [question["key"] for question in _intake_questions()]
    if body.question_key not in keys:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    answered = _answered_keys(db, patient.id) | {body.question_key}
    complete = all(key in answered for key in keys)
    db.add(
        IntakeAnswer(
            patient_id=patient.id,
            question_key=body.question_key,
            answer_value=body.answer_value,
            answered_at=datetime.now(UTC),
            is_complete=complete,
        )
    )
    db.commit()
    return with_notice({"patient_id": patient.id, "complete": complete})


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
    # The cutoff itself is an operational field (AC-010) and a plain date
    # (behaviour rules): stating it lets the leakage check prove the read holds
    # nothing dated on or after it (NFR-013, AC-029).
    return with_notice(
        {
            "patient_id": patient.id,
            "cutoff_date": _iso(cutoff_date(db, patient.id)),
            "items": _timeline_items(db, patient),
        }
    )


@router.get("/api/evaluation/runs/latest")
def latest_evaluation(user: Staff, db: Db) -> dict[str, Any]:
    """The latest evaluation report: sensitivity and PPV over the loaded
    cohort, with the notice, because its numbers come from the same synthetic
    cohort (AC-009). Staff only; the numbers are aggregates, never a
    patient's label."""
    from app.evaluation import latest_report

    return with_notice(latest_report(db))


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
