"""US-044-1: the shared bearer gate, the masked settings endpoint and /health.

No credential value is written here: the bearer is generated at run time.
"""

from __future__ import annotations

import json
import secrets

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import auth
from app.models import IngestRun


@pytest.fixture
def bearer(monkeypatch) -> str:
    token = secrets.token_urlsafe(24)
    monkeypatch.setenv("API_SECRET_KEY", token)
    monkeypatch.delenv("SECRET_KEY", raising=False)
    return token


@pytest.fixture
def headers(bearer: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {bearer}"}


# --------------------------------------------------------------- AC-146 the gate


@pytest.mark.parametrize("sent", [None, "", "Bearer wrong-token", "not-a-bearer", "Bearer "])
def test_ac146_a_missing_or_wrong_bearer_is_401(client: TestClient, bearer: str, sent):
    sent_headers = {} if sent is None else {"Authorization": sent}

    response = client.get("/api/admin/settings", headers=sent_headers)

    assert response.status_code == 401
    assert set(response.json()) == {"detail"}


def test_ac146_the_correct_bearer_passes(client: TestClient, headers: dict[str, str]):
    assert client.get("/api/admin/settings", headers=headers).status_code == 200


def test_ac146_the_dependency_refuses_without_a_configured_secret(monkeypatch):
    from fastapi import HTTPException

    monkeypatch.delenv("API_SECRET_KEY", raising=False)
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(HTTPException) as raised:
        auth.require_bearer("Bearer anything")
    assert raised.value.status_code == 401


def test_ac146_every_route_except_health_refuses_an_unauthenticated_request(
    client: TestClient, bearer: str
):
    for path in ("/api/worklist", "/api/patients/me/timeline", "/api/admin/ingest-runs"):
        assert client.get(path).status_code == 401, path


def test_ac144_health_stays_reachable_without_any_header(client: TestClient, bearer: str):
    assert client.get("/health").status_code == 200


# ------------------------------------------------------------- AC-144 the health body


def test_ac144_health_reports_ok_the_dataset_version_and_postgres_reachability(
    client: TestClient, db_session: Session
):
    body = client.get("/health").json()

    assert body["status"] == "ok"
    assert body["dataset_version"] is None  # no passed ingest run yet
    assert isinstance(body["services"]["db"], bool)


def test_ac144_health_reports_the_latest_passed_runs_dataset_version(
    client: TestClient, db_session: Session
):
    db_session.add(IngestRun(dataset_version="v-older", status="succeeded"))
    db_session.commit()
    db_session.add(IngestRun(dataset_version="v-failed", status="failed"))
    db_session.add(IngestRun(dataset_version="v-newest", status="succeeded"))
    db_session.commit()

    assert client.get("/health").json()["dataset_version"] == "v-newest"


# ------------------------------------------------------- AC-145 masked settings


def test_ac145_settings_report_connected_when_both_are_configured(
    client: TestClient, headers: dict[str, str], monkeypatch
):
    monkeypatch.setenv("ANTHROPIC_API_KEY", secrets.token_urlsafe(16))
    monkeypatch.setattr("app.routers.admin.database_reachable", lambda: True)

    body = client.get("/api/admin/settings", headers=headers).json()

    assert body["database"] == {"status": "connected"}
    assert body["llm"] == {"status": "connected"}
    assert body["dataset_version"] is None


def test_ac145_settings_report_not_configured_when_the_llm_key_is_absent(
    client: TestClient, headers: dict[str, str], monkeypatch
):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    body = client.get("/api/admin/settings", headers=headers).json()

    assert body["llm"] == {"status": "not-configured"}


def test_ac145_settings_report_not_configured_when_the_database_url_is_absent(
    client: TestClient, headers: dict[str, str], monkeypatch
):
    monkeypatch.delenv("DATABASE_URL", raising=False)

    body = client.get("/api/admin/settings", headers=headers).json()

    assert body["database"] == {"status": "not-configured"}


def test_ac145_no_credential_value_appears_anywhere_in_the_body(
    client: TestClient, headers: dict[str, str], monkeypatch
):
    llm_key = secrets.token_urlsafe(16)
    database_url = f"postgresql+psycopg://user:{secrets.token_urlsafe(8)}@host:5432/db"
    monkeypatch.setenv("ANTHROPIC_API_KEY", llm_key)
    monkeypatch.setenv("DATABASE_URL", database_url)

    raw = json.dumps(client.get("/api/admin/settings", headers=headers).json())

    assert llm_key not in raw
    assert database_url not in raw
    assert set(json.loads(raw)) == {
        "database",
        "llm",
        "dataset_version",
        "health",
        "credentials",
    }
