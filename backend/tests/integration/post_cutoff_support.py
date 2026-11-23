"""Helpers for the post-cutoff guardrail suite (US-034-1: AC-112, AC-113, NFR-013).

The suite runs the application's own guardrail over two things:

* the scoring inputs of every loaded patient, through
  `app.guardrails.leakage.check_cohort`;
* every rendered read the real API answers for those patients, through
  `app.guardrails.leakage.check_payload`.

Nothing is written into the database by hand. The cohort is whatever
GET /api/worklist already serves; a leakage fixture drop is ingested only when
the environment serves no cohort that could ever exercise the guarantee (no
patient holding an item dated on or after their own cutoff), and a 409 is
tolerated because ingest is serialised one run at a time (NFR-021).

Reading the store read-only is deliberate: the guardrail takes a database
session, and the suite has to know which patients hold post-cutoff items
before it can prove that none of them is ever rendered.
"""

from __future__ import annotations

import io
import os
import uuid
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import select

from tests.integration import fixtures_dataset as fx
from tests.integration.conftest import wait_for_run
from tests.integration.fixtures_leakage import LeakageDrop

INGEST_START = "/api/admin/ingest-runs"
WORKLIST = "/api/worklist"
EVALUATION = "/api/evaluation/runs/latest"


def db_session() -> Any:
    """A read-only session on the same database the API serves."""
    from app.database import SessionLocal

    return SessionLocal()


def objects(payload: Any) -> list[dict]:
    found: list[dict] = []
    if isinstance(payload, dict):
        found.append(payload)
        for value in payload.values():
            found.extend(objects(value))
    elif isinstance(payload, list):
        for item in payload:
            found.extend(objects(item))
    return found


def worklist_rows(api: TestClient, admin: dict[str, str]) -> list[dict]:
    response = api.get(WORKLIST, headers=admin)
    assert response.status_code == 200, (
        f"GET {WORKLIST} returned {response.status_code}: {response.text[:200]}"
    )
    return [
        row
        for row in objects(response.json())
        if row.get("patient_id") and row.get("dataset_patient_id")
    ]


def drain_ingest_queue() -> None:
    """Run whatever is on the ingest queue, as the deployed RQ worker would."""
    import redis
    from rq import Queue, SimpleWorker

    connection = redis.from_url(os.environ["REDIS_URL"])
    queue = Queue("ingest", connection=connection)
    SimpleWorker([queue], connection=connection).work(burst=True)


@dataclass
class StoredPatient:
    """One loaded patient, with what the store holds against their cutoff."""

    patient_id: str
    dataset_patient_id: str
    cutoff: date | None
    post_cutoff: list[tuple[str, str, str]] = field(default_factory=list)
    on_cutoff: list[tuple[str, str, str]] = field(default_factory=list)
    undated_family_history: list[tuple[str, str]] = field(default_factory=list)

    @property
    def markers(self) -> list[str]:
        """Strings that must never appear in anything rendered for this patient."""
        out: list[str] = []
        for event_id, _when, display in [*self.post_cutoff, *self.on_cutoff]:
            out.extend(text for text in (event_id, display) if text)
        return out


def stored_cohort(db) -> list[StoredPatient]:
    """Every loaded patient, and which of their stored items cross the cutoff."""
    from app.engine.inputs import FAMILY_HISTORY_TYPES, cutoff_date, item_date
    from app.models import Event, Patient

    cohort: list[StoredPatient] = []
    for patient in db.execute(select(Patient)).scalars():
        cutoff = cutoff_date(db, patient.id)
        entry = StoredPatient(
            patient_id=patient.id,
            dataset_patient_id=patient.dataset_patient_id,
            cutoff=cutoff,
        )
        events = db.execute(select(Event).where(Event.patient_id == patient.id)).scalars()
        for row in events:
            when = item_date(row.event_time)
            name = row.source_event_id or row.id
            display = row.display or ""
            if when is None:
                if str(row.event_type or "").lower() in FAMILY_HISTORY_TYPES:
                    entry.undated_family_history.append((name, display))
                continue
            if cutoff is None:
                continue
            if when == cutoff:
                entry.on_cutoff.append((name, when.isoformat(), display))
            elif when > cutoff:
                entry.post_cutoff.append((name, when.isoformat(), display))
        cohort.append(entry)
    return cohort


def _ingest_leakage_drop(api: TestClient, admin: dict[str, str]) -> None:
    """Load one drop that holds post-cutoff and on-cutoff items, tolerating a 409."""
    drop = LeakageDrop(uuid.uuid4().hex[:8])
    source_uri, _prefix = fx.upload_fixture_set(drop.files())
    drain_ingest_queue()
    response = api.post(
        INGEST_START,
        headers=admin,
        json={
            "dataset_version": f"qa-postcutoff-{drop.suffix}",
            "source_uri": source_uri,
            "seed": 34,
        },
    )
    drain_ingest_queue()
    if response.status_code == 409:
        return
    assert response.status_code in (200, 202), (
        f"starting the guardrail cohort's ingest run returned {response.status_code}: "
        f"{response.text[:300]}"
    )
    wait_for_run(api, admin, response.json()["run_id"])
    drain_ingest_queue()


_STATE: dict[str, Any] = {}


def loaded_cohort(api: TestClient, admin: dict[str, str]) -> list[StoredPatient]:
    """The cohort this suite sweeps: the loaded one, ingesting only if it cannot
    exercise the guarantee at all."""
    cached = _STATE.get("cohort")
    if isinstance(cached, list):
        return cached

    rows = worklist_rows(api, admin)
    known = {str(row["patient_id"]) for row in rows}
    db = db_session()
    try:
        cohort = [entry for entry in stored_cohort(db) if entry.patient_id in known]
    finally:
        db.close()

    if not any(entry.post_cutoff or entry.on_cutoff for entry in cohort):
        _ingest_leakage_drop(api, admin)
        rows = worklist_rows(api, admin)
        known = {str(row["patient_id"]) for row in rows}
        db = db_session()
        try:
            cohort = [entry for entry in stored_cohort(db) if entry.patient_id in known]
        finally:
            db.close()

    assert cohort, (
        f"no patient is visible through GET {WORKLIST}, so the post-cutoff guardrail "
        "cannot be run across a loaded cohort"
    )
    _STATE["cohort"] = cohort
    return cohort


def adversarial(cohort: list[StoredPatient]) -> list[StoredPatient]:
    """The loaded patients whose store holds an item on or after their cutoff."""
    return [entry for entry in cohort if entry.post_cutoff or entry.on_cutoff]


def rendered_reads(api: TestClient, admin: dict[str, str], patient_id: str) -> dict[str, Any]:
    """Every JSON read the API renders for this patient, route -> payload."""
    payloads: dict[str, Any] = {}
    for path in (
        f"/api/cases/{patient_id}/timeline",
        f"/api/cases/{patient_id}",
        EVALUATION,
    ):
        response = api.get(path, headers=admin)
        assert response.status_code == 200, (
            f"GET {path} returned {response.status_code}, so the guardrail cannot be "
            f"run over what it renders: {response.text[:200]}"
        )
        payloads[path] = response.json()
    return payloads


def pdf_text(data: bytes) -> str:
    """All text of a rendered PDF export, pages joined."""
    import pypdf

    reader = pypdf.PdfReader(io.BytesIO(data))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def referral_packet_text(api: TestClient, admin: dict[str, str], patient_id: str) -> str:
    response = api.get(f"/api/cases/{patient_id}/referral-packet.pdf", headers=admin)
    assert response.status_code == 200, (
        f"GET /api/cases/{patient_id}/referral-packet.pdf returned "
        f"{response.status_code}: {response.text[:200]}"
    )
    return pdf_text(response.content)


def patient_token(api: TestClient) -> str:
    """A patient-role session token, through the one sign-in route."""
    email = os.environ.get("SMOKE_TEST_EMAIL")
    password = os.environ.get("SMOKE_TEST_PASSWORD")
    assert email and password, (
        "SMOKE_TEST_EMAIL and SMOKE_TEST_PASSWORD are not set: the platform sets them "
        "for every run and the backend creates that patient account at startup."
    )
    response = api.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, (
        f"the patient-role account cannot sign in: {response.status_code} {response.text[:200]}"
    )
    return str(response.json()["token"])
