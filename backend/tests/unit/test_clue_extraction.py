"""US-015-1: the free-text clue extractor and its background job.

Every clue name in these assertions is read back from the active condition
pack, never spelled out here (NFR-019). The Anthropic client is substituted
with a fake: a unit test never calls the real API.
"""

from __future__ import annotations

import json
import secrets
import uuid
from typing import Any

import pytest
from sqlalchemy.orm import Session

from app import clue_extraction
from app.models import Note, NoteFinding, Patient, User
from app.security import hash_password
from app.sessions import issue_session

JOBS = "/api/admin/jobs"
VERSION = "unit-clues"


class _FakeBlock:
    def __init__(self, text: str) -> None:
        self.text = text


class _FakeResponse:
    def __init__(self, text: str) -> None:
        self.content = [_FakeBlock(text)]


class _FakeMessages:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload
        self.calls = 0

    def create(self, **_kwargs: Any) -> _FakeResponse:
        self.calls += 1
        return _FakeResponse(json.dumps(self._payload))


class _FakeClient:
    """An Anthropic stand-in that answers with one fixed JSON payload."""

    def __init__(self, findings: list[dict[str, Any]]) -> None:
        self.messages = _FakeMessages({"findings": findings})


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
        note_type="imaging_report",
        text=text,
    )
    db.add(note)
    db.commit()
    return note


@pytest.fixture
def clues(db_session: Session) -> dict[str, dict[str, Any]]:
    found = clue_extraction.target_clues(db_session)
    assert found, "the active pack declares no free-text clues"
    return found


def _open_clues(clues: dict[str, dict[str, Any]]) -> list[str]:
    """The pack's clues that declare no closed value set, in a stable order."""
    keys = sorted(key for key, item in clues.items() if not item.get("values"))
    assert keys, "the pack declares no free-text clue without a value set"
    return keys


def test_ac049_a_found_clue_is_returned_with_its_sentence_and_source_ref(
    db_session: Session, clues: dict[str, dict[str, Any]]
) -> None:
    clue_type = _open_clues(clues)[0]
    sentence = "The sacroiliac joints show changes consistent with inflammation."
    note = _note(db_session, _patient(db_session), f"History reviewed. {sentence} No fracture.")
    client = _FakeClient([{"clue_type": clue_type, "quoted_sentence": sentence}])

    findings = clue_extraction.extract_from_note(note, clues, client)

    assert [item["clue_type"] for item in findings] == [clue_type]
    assert findings[0]["quoted_sentence"] == sentence
    assert findings[0]["source_ref"] == note.source_ref


def test_ac049_every_target_clue_found_in_one_report_is_its_own_finding(
    db_session: Session, clues: dict[str, dict[str, Any]]
) -> None:
    first, second = _open_clues(clues)[:2]
    one = "Sclerosis is seen on the iliac side only."
    two = "No erosions are identified."
    note = _note(db_session, _patient(db_session), f"{one} {two}")
    client = _FakeClient(
        [
            {"clue_type": first, "quoted_sentence": one},
            {"clue_type": second, "quoted_sentence": two},
        ]
    )

    findings = clue_extraction.extract_from_note(note, clues, client)

    assert sorted(item["clue_type"] for item in findings) == sorted([first, second])
    assert all(item["quoted_sentence"] in note.text for item in findings)
    assert {item["source_ref"] for item in findings} == {note.source_ref}


def test_ac049_a_declared_value_set_is_stored_with_the_finding(
    db_session: Session, clues: dict[str, dict[str, Any]]
) -> None:
    valued = [key for key, item in clues.items() if item.get("values")]
    assert valued, "the pack declares no clue with a closed value set"
    clue_type = valued[0]
    value = str(clues[clue_type]["values"][0])
    sentence = "Findings are described in the report above."
    note = _note(db_session, _patient(db_session), sentence)
    client = _FakeClient(
        [{"clue_type": clue_type, "finding_value": value, "quoted_sentence": sentence}]
    )

    findings = clue_extraction.extract_from_note(note, clues, client)

    assert findings[0]["finding_value"] == value


def test_ac049_with_no_model_configured_the_packs_wording_still_finds_each_clue(
    db_session: Session, clues: dict[str, dict[str, Any]]
) -> None:
    """AC-049: with no language model configured the extractor falls back to the
    wording the pack declares, quoting whole sentences of the note."""
    sentences = [
        "MRI of the sacroiliac joints demonstrates active sacroiliitis with bone marrow oedema.",
        "Sclerosis is confined to the iliac side of the joint.",
        "No erosions are identified.",
        "Symptoms began three months postpartum after her second delivery.",
    ]
    note = _note(db_session, _patient(db_session), " ".join(sentences))

    findings = clue_extraction.extract_from_note(note, clues, None)

    declared = {key for key, item in clues.items() if item.get("match_any")}
    assert {item["clue_type"] for item in findings} == declared
    assert all(item["quoted_sentence"] in sentences for item in findings)
    assert {item["source_ref"] for item in findings} == {note.source_ref}


def test_ac050_with_no_model_configured_a_clue_free_note_yields_nothing(
    db_session: Session, clues: dict[str, dict[str, Any]]
) -> None:
    """AC-050: the fallback invents nothing for a note carrying no target clue."""
    note = _note(
        db_session,
        _patient(db_session),
        "Attended for a routine medication review. No new concerns were raised today.",
    )

    assert clue_extraction.extract_from_note(note, clues, None) == []


def test_ac050_a_note_with_no_target_clue_yields_nothing_and_is_still_processed(
    db_session: Session, clues: dict[str, dict[str, Any]]
) -> None:
    patient = _patient(db_session)
    note = _note(db_session, patient, "Routine review. Nothing of note today.")
    client = _FakeClient([])

    findings = clue_extraction.process_note(db_session, note, clues, client)

    assert findings == []
    assert db_session.query(NoteFinding).count() == 0
    assert note.processed_at is not None


def test_ac050_a_sentence_not_in_the_note_is_never_stored(
    db_session: Session, clues: dict[str, dict[str, Any]]
) -> None:
    clue_type = _open_clues(clues)[0]
    note = _note(db_session, _patient(db_session), "The study is unremarkable.")
    client = _FakeClient(
        [{"clue_type": clue_type, "quoted_sentence": "The sacroiliac joints are inflamed."}]
    )

    findings = clue_extraction.process_note(db_session, note, clues, client)

    assert findings == []
    assert db_session.query(NoteFinding).count() == 0
    assert note.processed_at is not None


def test_ac050_a_clue_the_pack_does_not_declare_is_discarded(
    db_session: Session, clues: dict[str, dict[str, Any]]
) -> None:
    sentence = "Sclerosis is seen on the iliac side only."
    note = _note(db_session, _patient(db_session), sentence)
    client = _FakeClient([{"clue_type": "invented_clue", "quoted_sentence": sentence}])

    assert clue_extraction.extract_from_note(note, clues, client) == []


def test_ac049_the_cohort_run_persists_a_finding_per_note_and_counts_every_note(
    db_session: Session,
) -> None:
    patient = _patient(db_session)
    sentence = "Sclerosis is seen on the iliac side only."
    _note(db_session, patient, sentence)
    _note(db_session, patient, "Nothing of note.")
    clue_type = _open_clues(clue_extraction.target_clues(db_session))[0]
    client = _FakeClient([{"clue_type": clue_type, "quoted_sentence": sentence}])

    report = clue_extraction.extract_cohort(db_session, client=client)

    assert report["notes_processed"] == 2
    assert report["findings"] == 1
    assert db_session.query(NoteFinding).count() == 1
    assert all(note.processed_at is not None for note in db_session.query(Note).all())


def test_nfr006_running_the_extraction_twice_leaves_the_same_findings(
    db_session: Session,
) -> None:
    patient = _patient(db_session)
    sentence = "Sclerosis is seen on the iliac side only."
    _note(db_session, patient, sentence)
    clue_type = _open_clues(clue_extraction.target_clues(db_session))[0]
    client = _FakeClient([{"clue_type": clue_type, "quoted_sentence": sentence}])

    clue_extraction.extract_cohort(db_session, client=client)
    clue_extraction.extract_cohort(db_session, client=client)

    assert db_session.query(NoteFinding).count() == 1


def test_nfr006_the_extractor_reports_progress_while_it_runs(db_session: Session) -> None:
    patient = _patient(db_session)
    for index in range(4):
        _note(db_session, patient, f"Note {index}.")
    seen: list[float] = []

    clue_extraction.extract_cohort(db_session, progress=seen.append, client=_FakeClient([]))

    assert seen == sorted(seen)
    assert seen[-1] == 100.0


# --------------------------------------------------------------- the job routes


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


def test_nfr006_starting_the_job_is_401_unauthenticated(client, db_session: Session) -> None:
    response = client.post(JOBS, json={"kind": "clue_extraction"})
    assert response.status_code == 401
    assert set(response.json()) == {"detail"}


def test_nfr006_starting_the_job_is_403_for_a_non_admin(client, db_session: Session) -> None:
    _, token = _user(db_session, "patient")
    response = client.post(
        JOBS, json={"kind": "clue_extraction"}, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403


def test_nfr006_an_unknown_job_kind_is_422(client, db_session: Session) -> None:
    _, token = _user(db_session, "admin")
    response = client.post(
        JOBS, json={"kind": "not-a-kind"}, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 422


def test_nfr006_an_unknown_job_id_is_404(client, db_session: Session) -> None:
    _, token = _user(db_session, "admin")
    response = client.get(f"{JOBS}/{uuid.uuid4()}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404


def test_nfr006_the_job_is_queued_with_its_kind_and_a_job_id(
    client, db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, token = _user(db_session, "admin")
    queued: dict[str, Any] = {}

    def fake_enqueue(func, *args: Any, **kwargs: Any) -> str:
        queued["func"] = func
        queued["meta"] = kwargs.get("meta")
        return "job-1"

    monkeypatch.setattr("app.jobs.enqueue", fake_enqueue)
    response = client.post(
        JOBS, json={"kind": "clue_extraction"}, headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 202
    body = response.json()
    assert body["job_id"] == "job-1"
    assert body["kind"] == "clue_extraction"
    assert body["status"]
    assert queued["func"] is clue_extraction.run_clue_extraction


def test_nfr006_the_job_read_reports_kind_progress_and_result(
    client, db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, token = _user(db_session, "admin")
    monkeypatch.setattr(
        "app.jobs.status",
        lambda job_id: {
            "job_id": job_id,
            "kind": "clue_extraction",
            "status": "started",
            "progress_pct": 40.0,
            "result": None,
        },
    )
    response = client.get(f"{JOBS}/job-1", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert body["kind"] == "clue_extraction"
    assert body["progress_pct"] == 40.0
    assert body["result"] is None
