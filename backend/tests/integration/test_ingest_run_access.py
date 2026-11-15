"""US-001-6: who may start and read an ingest run, and what an unknown run returns.

These are the error paths around the same two endpoints the acceptance criteria
exercise (AC-001..AC-004): a report nobody may read, or a run id that does not
exist, must answer with the shapes the behaviour rules fix.

Both routes are guarded by the shared bearer the contract fixes (the platform's
`SECRET_KEY`, sent as `Authorization: Bearer <SECRET_KEY>`), not by a sign-in
route: no login endpoint is part of this contract, so the token is taken from
that setting here. The value is generated at run time, never written down.
"""

from __future__ import annotations

import os
import secrets
import uuid

from fastapi.testclient import TestClient


def shared_bearer_headers() -> dict[str, str]:
    """The shared bearer every admin route in this contract requires."""
    token = os.environ.get("SECRET_KEY")
    if not token:
        token = secrets.token_urlsafe(32)
        os.environ["SECRET_KEY"] = token
    return {"Authorization": f"Bearer {token}"}


def test_ac002_the_report_requires_a_bearer_token(api: TestClient) -> None:
    """AC-002: no token means 401, with the one error shape."""
    response = api.get(f"/api/admin/ingest-runs/{uuid.uuid4()}")

    assert response.status_code == 401
    assert set(response.json()) == {"detail"}


def test_ac001_starting_a_run_requires_a_bearer_token(api: TestClient) -> None:
    """AC-001: an unauthenticated start is refused with 401."""
    response = api.post(
        "/api/admin/ingest-runs",
        json={"dataset_version": "v0.1", "source_uri": "s3://nowhere/x", "seed": 1},
    )

    assert response.status_code == 401
    assert set(response.json()) == {"detail"}


def test_ac002_an_unknown_run_id_is_404(api: TestClient) -> None:
    """AC-002: a run id that was never created is not found, not an empty report."""
    response = api.get(f"/api/admin/ingest-runs/{uuid.uuid4()}", headers=shared_bearer_headers())

    assert response.status_code == 404
    assert set(response.json()) == {"detail"}


def test_ac001_a_start_without_a_dataset_version_is_422(api: TestClient) -> None:
    """AC-001: dataset_version is required, so omitting it is a validation error."""
    response = api.post(
        "/api/admin/ingest-runs",
        headers=shared_bearer_headers(),
        json={"source_uri": "s3://nowhere/x", "seed": 1},
    )

    assert response.status_code == 422
    assert set(response.json()) == {"detail"}
