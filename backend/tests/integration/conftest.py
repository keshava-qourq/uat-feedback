"""Fixtures for the ingest-run acceptance tests (US-001-6).

These criteria are about the real thing: the real API, the real PostgreSQL the
sandbox runs and the real Redis job queue. The suite-wide `client` fixture
hands the application an in-memory SQLite of its own, which a background
worker could never see, so this package adds an `api` client that talks to the
configured `DATABASE_URL` and runs the application's startup (which creates the
tables and seeds the bootstrap admin) exactly as a deployment does.

Nothing that can fail an acceptance criterion happens in a fixture: signing in
and running an ingest are plain helpers called from the test body, so a
criterion the code does not meet yet is reported as a failing test rather than
as a fixture error that proves nothing.

The admin password is generated here at run time and only ever lives in this
process's environment -- no credential is written into the repository.
"""

from __future__ import annotations

import os
import secrets
import time
import uuid
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def api() -> Iterator[TestClient]:
    """The application as deployed: real database, real queue, startup run."""
    os.environ.setdefault("BOOTSTRAP_ADMIN_EMAIL", f"qa-admin-{uuid.uuid4().hex[:8]}@example.test")
    os.environ.setdefault("BOOTSTRAP_ADMIN_PASSWORD", secrets.token_urlsafe(24))
    from app.main import app

    with TestClient(app) as client:
        yield client


def admin_headers(api: TestClient) -> dict[str, str]:
    """Bearer headers for the bootstrap admin, obtained through POST /api/auth/login.

    Called from the test body on purpose: when sign-in is not there yet the
    criterion fails with this message instead of erroring during setup.
    """
    email = os.environ.get("BOOTSTRAP_ADMIN_EMAIL")
    password = os.environ.get("BOOTSTRAP_ADMIN_PASSWORD")
    assert email and password, (
        "BOOTSTRAP_ADMIN_EMAIL and BOOTSTRAP_ADMIN_PASSWORD are not set: the platform "
        "sets them for every run and the backend creates that admin at startup."
    )
    response = api.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, (
        f"the bootstrap admin cannot sign in: {response.status_code} {response.text[:200]}"
    )
    return {"Authorization": f"Bearer {response.json()['token']}"}


TERMINAL_STATUSES = {"completed", "complete", "succeeded", "success", "failed", "error"}


def start_ingest(
    api: TestClient, headers: dict[str, str], *, dataset_version: str, source_uri: str, seed: int
) -> dict:
    """POST /api/admin/ingest-runs and return its body: {run_id, job_id}."""
    response = api.post(
        "/api/admin/ingest-runs",
        headers=headers,
        json={"dataset_version": dataset_version, "source_uri": source_uri, "seed": seed},
    )
    assert response.status_code in (200, 202), (
        f"starting an ingest run returned {response.status_code}: {response.text[:300]}"
    )
    body = response.json()
    assert "run_id" in body, f"the start response has no run_id: {body}"
    return body


def wait_for_run(
    api: TestClient, headers: dict[str, str], run_id: str, timeout: float = 120.0
) -> dict:
    """Poll GET /api/admin/ingest-runs/{run_id} until the run reaches a terminal status."""
    deadline = time.monotonic() + timeout
    body: dict = {}
    while time.monotonic() < deadline:
        response = api.get(f"/api/admin/ingest-runs/{run_id}", headers=headers)
        assert response.status_code == 200, (
            f"the ingest report returned {response.status_code}: {response.text[:300]}"
        )
        body = response.json()
        status = str(body.get("run", {}).get("status", "")).lower()
        if status in TERMINAL_STATUSES:
            return body
        time.sleep(1.0)
    raise AssertionError(
        f"ingest run {run_id} did not finish within {timeout:.0f}s; last report: {str(body)[:300]}"
    )


def files_by_name(report: dict) -> dict[str, dict]:
    """The report's per-file rows, keyed by the file name they carry."""
    rows = report.get("files") or []
    return {str(row.get("file_name", "")).split("/")[-1]: row for row in rows}
