"""US-001-4: the two admin ingest-run routes, against a stubbed job.

The job itself is proved in test_ingest_job.py; here it is replaced by a stub
so the routes' own behaviour -- response shapes, 401, 404 and the
one-run-at-a-time 409 -- is what each test measures.
"""

from __future__ import annotations

import secrets
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import IngestFileResult, IngestRun
from app.routers import ingest_runs

START_BODY = {"dataset_version": "v-test", "source_uri": "/tmp/drop", "seed": 7}


@pytest.fixture
def bearer(monkeypatch) -> str:
    token = secrets.token_urlsafe(24)
    monkeypatch.setenv("SECRET_KEY", token)
    return token


@pytest.fixture
def headers(bearer: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {bearer}"}


@pytest.fixture(autouse=True)
def stub_job(monkeypatch):
    """The queue is never touched: the route only has to hand the job over."""
    calls: list[tuple] = []

    def fake_enqueue(run_id, dataset_version, source_uri, seed=None):
        calls.append((run_id, dataset_version, source_uri, seed))
        return f"job-{run_id}"

    monkeypatch.setattr(ingest_runs, "enqueue_ingest", fake_enqueue)
    return calls


def test_ac001_start_returns_202_with_the_run_summary(
    client: TestClient, headers: dict[str, str], stub_job
):
    response = client.post("/api/admin/ingest-runs", headers=headers, json=START_BODY)

    assert response.status_code == 202
    body = response.json()
    assert set(body) >= {"run_id", "status", "dataset_version", "seed", "started_at"}
    assert uuid.UUID(body["run_id"])
    assert body["status"] == "queued"
    assert body["dataset_version"] == "v-test"
    assert body["seed"] == 7
    assert body["started_at"]
    assert stub_job == [(body["run_id"], "v-test", "/tmp/drop", 7)]


def test_ac001_a_second_start_while_a_run_is_in_progress_is_409(
    client: TestClient, headers: dict[str, str]
):
    first = client.post("/api/admin/ingest-runs", headers=headers, json=START_BODY)
    assert first.status_code == 202

    second = client.post("/api/admin/ingest-runs", headers=headers, json=START_BODY)

    assert second.status_code == 409
    assert set(second.json()) == {"detail"}


def test_ac002_the_report_carries_the_run_summary_and_a_line_per_file(
    client: TestClient, headers: dict[str, str], db_session: Session
):
    started = client.post("/api/admin/ingest-runs", headers=headers, json=START_BODY).json()
    run = db_session.get(IngestRun, started["run_id"])
    run.status = "failed"
    run.patient_count = 3
    db_session.add_all(
        [
            IngestFileResult(
                ingest_run_id=run.id,
                file_name="patients.csv",
                status="pass",
                rows_loaded=3,
                rows_rejected=0,
            ),
            IngestFileResult(
                ingest_run_id=run.id,
                file_name="events.csv",
                status="fail",
                rows_loaded=0,
                rows_rejected=0,
                error_detail="events.csv: required column 'source_ref' is missing",
            ),
        ]
    )
    db_session.commit()

    body = client.get(f"/api/admin/ingest-runs/{run.id}", headers=headers).json()

    assert body["run_id"] == run.id
    assert body["status"] == "failed"
    assert body["dataset_version"] == "v-test"
    assert body["seed"] == 7
    assert body["patient_count"] == 3
    assert body["started_at"]
    assert body["finished_at"] is None
    rows = {row["file"]: row for row in body["files"]}
    assert set(rows) == {"patients.csv", "events.csv"}
    assert set(rows["patients.csv"]) >= {
        "file",
        "status",
        "rows_loaded",
        "rows_rejected",
        "error",
    }
    assert rows["patients.csv"]["rows_loaded"] == 3
    assert rows["patients.csv"]["error"] is None


def test_ac003_a_failed_files_error_names_the_file_and_the_column(
    client: TestClient, headers: dict[str, str], db_session: Session
):
    started = client.post("/api/admin/ingest-runs", headers=headers, json=START_BODY).json()
    db_session.add(
        IngestFileResult(
            ingest_run_id=started["run_id"],
            file_name="events.csv",
            status="fail",
            error_detail="events.csv: required column 'source_ref' is missing",
        )
    )
    db_session.commit()

    body = client.get(f"/api/admin/ingest-runs/{started['run_id']}", headers=headers).json()

    failed = next(row for row in body["files"] if row["status"] == "fail")
    assert "events.csv" in failed["error"]
    assert "source_ref" in failed["error"]


def test_ac002_an_unknown_run_id_is_404(client: TestClient, headers: dict[str, str]):
    response = client.get(f"/api/admin/ingest-runs/{uuid.uuid4()}", headers=headers)

    assert response.status_code == 404
    assert set(response.json()) == {"detail"}


@pytest.mark.parametrize("sent", [None, "Bearer wrong-token", "not-a-bearer"])
def test_ac004_both_routes_need_the_shared_bearer(client: TestClient, bearer: str, sent):
    headers = {} if sent is None else {"Authorization": sent}

    post = client.post("/api/admin/ingest-runs", headers=headers, json=START_BODY)
    get = client.get(f"/api/admin/ingest-runs/{uuid.uuid4()}", headers=headers)

    assert post.status_code == 401
    assert get.status_code == 401
    assert set(post.json()) == {"detail"}
