"""US-015-2: extracted findings as evidence, and the admin extraction report.

Every clue name is read back from the active condition pack (NFR-019); no
note text is re-stored and the note behind an evidence item is reached
through the link the evidence carries.
"""

from __future__ import annotations

import secrets
import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy.orm import Session

from app import clue_extraction, extraction_report
from app.labels import PatientLabel
from app.models import Note, NoteFinding, Patient, User
from app.security import hash_password
from app.sessions import issue_session

REPORT = "/api/admin/extraction-report"
VERSION = "unit-report"


def _patient(db: Session) -> Patient:
    patient = Patient(
        dataset_patient_id=f"P-{uuid.uuid4().hex[:6]}",
        dataset_version=VERSION,
        display_name="Ada",
    )
    db.add(patient)
    db.commit()
    return patient


def _note(db: Session, patient: Patient, text: str) -> Note:
    note = Note(
        patient_id=patient.id,
        source_ref=f"note:{uuid.uuid4().hex[:8]}",
        note_time=datetime(2019, 3, 4, tzinfo=UTC),
        note_type="imaging_report",
        text=text,
        processed_at=datetime.now(UTC),
    )
    db.add(note)
    db.commit()
    return note


def _finding(db: Session, note: Note, clue_type: str, sentence: str) -> NoteFinding:
    row = NoteFinding(
        note_id=note.id,
        patient_id=note.patient_id,
        clue_type=clue_type,
        finding_value=None,
        quoted_sentence=sentence,
        source_ref=note.source_ref,
        extractor_model="fake-model",
    )
    db.add(row)
    db.commit()
    return row


def _user(db: Session, role: str) -> tuple[User, str]:
    user = User(
        email=f"{role}-{uuid.uuid4().hex[:6]}@example.invalid",
        password_hash=hash_password(secrets.token_urlsafe(16)),
        role=role,
        is_active=True,
        must_set_password=False,
    )
    db.add(user)
    db.commit()
    return user, issue_session(db, user)


@pytest.fixture
def clue_type(db_session: Session) -> str:
    clues = clue_extraction.target_clues(db_session)
    assert clues, "the active pack declares no free-text clues"
    return sorted(clues)[0]


# ------------------------------------------------------------------- AC-051


def test_ac051_an_evidence_item_exposes_its_quote_and_a_link_to_the_full_note(
    db_session: Session, clue_type: str
) -> None:
    patient = _patient(db_session)
    sentence = "Sclerosis is confined to the iliac side of the joint."
    note = _note(db_session, patient, f"{sentence} Nothing else of note.")
    _finding(db_session, note, clue_type, sentence)

    items = extraction_report.finding_evidence(db_session, patient.id)

    assert len(items) == 1
    item = items[0]
    assert item["quoted_sentence"] == sentence
    assert item["source_ref"] == note.source_ref
    assert item["note_link"].endswith(note.source_ref)
    assert item["note_found"] is True
    # The note text itself is never re-stored on the evidence item.
    assert note.text not in str(item)


def test_ac051_the_evidence_link_resolves_to_the_full_note(
    client, db_session: Session, clue_type: str
) -> None:
    _, token = _user(db_session, "clinician")
    patient = _patient(db_session)
    sentence = "No erosions are identified."
    note = _note(db_session, patient, f"{sentence} The study is otherwise normal.")
    _finding(db_session, note, clue_type, sentence)

    case = client.get(f"/api/cases/{patient.id}", headers={"Authorization": f"Bearer {token}"})
    assert case.status_code == 200
    evidence = case.json()["extracted_evidence"]
    assert evidence and evidence[0]["quoted_sentence"] == sentence

    full = client.get(evidence[0]["note_link"], headers={"Authorization": f"Bearer {token}"})
    assert full.status_code == 200
    assert full.json()["text"] == note.text


def test_ac051_a_post_cutoff_note_yields_no_evidence_item(
    db_session: Session, clue_type: str
) -> None:
    patient = _patient(db_session)
    db_session.add(
        PatientLabel(
            patient_id=patient.id,
            dataset_version=VERSION,
            split="train",
            eval_cutoff_date=datetime(2018, 1, 1, tzinfo=UTC).date(),
        )
    )
    db_session.commit()
    sentence = "No erosions are identified."
    note = _note(db_session, patient, sentence)
    _finding(db_session, note, clue_type, sentence)

    assert extraction_report.finding_evidence(db_session, patient.id) == []


# ------------------------------------------------------------------- AC-052


def test_ac052_the_report_counts_notes_processed_and_findings_per_clue_type(
    db_session: Session, clue_type: str
) -> None:
    patient = _patient(db_session)
    sentence = "Sclerosis is confined to the iliac side of the joint."
    first = _note(db_session, patient, sentence)
    _note(db_session, patient, "Routine review, nothing of note.")
    unprocessed = Note(
        patient_id=patient.id,
        source_ref=f"note:{uuid.uuid4().hex[:8]}",
        note_type="clinic_note",
        text="Not looked at yet.",
    )
    db_session.add(unprocessed)
    db_session.commit()
    _finding(db_session, first, clue_type, sentence)

    report = extraction_report.extraction_report(db_session)

    assert report["notes_processed"] == 2
    counts = {row["clue_type"]: row["count"] for row in report["findings_by_clue_type"]}
    assert counts[clue_type] == 1
    assert set(counts) >= set(clue_extraction.target_clues(db_session))
    assert all(isinstance(value, int) for value in counts.values())


def test_ac052_the_report_states_the_templated_text_caveat_and_dataset_version(
    db_session: Session,
) -> None:
    report = extraction_report.extraction_report(db_session)

    caveat = report["caveat"].lower()
    assert "template" in caveat and "easier" in caveat
    assert "dataset_version" in report


def test_ac052_the_route_is_401_unauthenticated(client, db_session: Session) -> None:
    response = client.get(REPORT)
    assert response.status_code == 401
    assert set(response.json()) == {"detail"}


def test_ac052_the_route_is_403_for_a_non_admin(client, db_session: Session) -> None:
    _, token = _user(db_session, "clinician")
    response = client.get(REPORT, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
    assert set(response.json()) == {"detail"}


def test_ac052_the_payload_carries_the_synthetic_data_notice(
    client, db_session: Session, clue_type: str
) -> None:
    from app.notice import SYNTHETIC_DATA_NOTICE

    _, token = _user(db_session, "admin")
    response = client.get(REPORT, headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert body["notice"] == SYNTHETIC_DATA_NOTICE
    assert isinstance(body["notes_processed"], int)
    assert isinstance(body["findings_by_clue_type"], list)
