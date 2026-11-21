"""US-FIX-1: an ingest run is only "in progress" while a job actually backs it.

The one-run-at-a-time rule (NFR-021) is enforced by a 409 against any row left
in queued/running. A row whose job has crashed, been reaped, or simply lost
its Redis keys -- every key on this project's Redis is disposable -- backs no
work at all, so leaving it "in progress" locked ingest out for the whole
30-minute stale window and failed every later ingest-dependent request.

The queue is therefore the authority on which runs are live, with the row's
age as the fallback for when the queue cannot be read at all.
"""

from __future__ import annotations

import secrets
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import IngestRun
from app.routers import ingest_runs

START_BODY = {"dataset_version": "v-test", "source_uri": "/tmp/drop", "seed": 7}


@pytest.fixture
def headers(monkeypatch) -> dict[str, str]:
    token = secrets.token_urlsafe(24)
    monkeypatch.setenv("SECRET_KEY", token)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def stub_job(monkeypatch):
    """The route only has to hand the job over; the queue itself is stubbed."""
    monkeypatch.setattr(ingest_runs, "enqueue_ingest", lambda *a, **k: f"job-{uuid.uuid4().hex}")


def _orphan(db: Session, *, status: str, age: timedelta) -> IngestRun:
    """A row in progress whose job is nowhere on the queue."""
    run = IngestRun(
        dataset_version="v-orphan",
        status=status,
        started_at=datetime.now(UTC) - age,
    )
    db.add(run)
    db.commit()
    return run


@pytest.mark.parametrize("status", ["queued", "running"])
def test_an_orphaned_run_does_not_block_a_new_start_and_is_closed_off(
    client: TestClient, headers: dict[str, str], db_session: Session, monkeypatch, status: str
):
    """A row the queue does not know about is abandoned, however recent it is."""
    monkeypatch.setattr(ingest_runs, "active_run_ids", set)
    orphan = _orphan(db_session, status=status, age=timedelta(minutes=1))

    response = client.post("/api/admin/ingest-runs", headers=headers, json=START_BODY)

    assert response.status_code == 202
    db_session.expire_all()
    assert db_session.get(IngestRun, orphan.id).status == "failed"
    assert db_session.get(IngestRun, orphan.id).finished_at is not None


def test_nfr021_a_run_whose_job_is_still_on_the_queue_is_a_409(
    client: TestClient, headers: dict[str, str], db_session: Session, monkeypatch
):
    """A genuinely live run still serialises ingest: two runs may not race."""
    live = _orphan(db_session, status="running", age=timedelta(minutes=5))
    monkeypatch.setattr(ingest_runs, "active_run_ids", lambda: {live.id})

    response = client.post("/api/admin/ingest-runs", headers=headers, json=START_BODY)

    assert response.status_code == 409
    assert set(response.json()) == {"detail"}
    db_session.expire_all()
    assert db_session.get(IngestRun, live.id).status == "running"


def test_a_run_started_moments_ago_is_trusted_before_its_job_reaches_the_queue(
    client: TestClient, headers: dict[str, str], db_session: Session, monkeypatch
):
    """The row is committed just before the job is enqueued; that gap is not abandonment."""
    monkeypatch.setattr(ingest_runs, "active_run_ids", set)
    fresh = _orphan(db_session, status="queued", age=timedelta(seconds=1))

    response = client.post("/api/admin/ingest-runs", headers=headers, json=START_BODY)

    assert response.status_code == 409
    db_session.expire_all()
    assert db_session.get(IngestRun, fresh.id).status == "queued"


def test_an_unreadable_queue_falls_back_to_the_age_of_the_row(
    client: TestClient, headers: dict[str, str], db_session: Session, monkeypatch
):
    """A queue that cannot be read proves nothing, so only a long-stale row is closed."""
    monkeypatch.setattr(ingest_runs, "active_run_ids", lambda: None)
    recent = _orphan(db_session, status="running", age=timedelta(minutes=1))

    blocked = client.post("/api/admin/ingest-runs", headers=headers, json=START_BODY)
    assert blocked.status_code == 409

    recent.started_at = datetime.now(UTC) - (ingest_runs.STALE_AFTER + timedelta(minutes=1))
    db_session.commit()

    allowed = client.post("/api/admin/ingest-runs", headers=headers, json=START_BODY)
    assert allowed.status_code == 202
    db_session.expire_all()
    assert db_session.get(IngestRun, recent.id).status == "failed"
