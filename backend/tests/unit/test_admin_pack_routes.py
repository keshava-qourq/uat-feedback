"""US-007-2: the condition pack through the admin API (AC-020, AC-022, NFR-019)."""

from __future__ import annotations

import copy
import secrets
import uuid

import pytest
import yaml
from sqlalchemy.orm import Session

from app.models import User
from app.pack import registry
from app.security import hash_password
from app.sessions import issue_session

PACK = "/api/admin/pack"


@pytest.fixture(autouse=True)
def _clean_registry():
    registry.reload()
    yield
    registry.reload()


def _user(db: Session, role: str) -> User:
    user = User(
        email=f"{role}-{uuid.uuid4().hex[:8]}@example.test",
        password_hash=hash_password(secrets.token_urlsafe(16)),
        role=role,
        is_active=True,
        must_set_password=False,
    )
    db.add(user)
    db.commit()
    return user


def _headers(db: Session, role: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {issue_session(db, _user(db, role))}"}


@pytest.fixture
def raw() -> dict:
    key = registry.list_packs()[0]
    return yaml.safe_load((registry.PACKS_DIR / f"{key}.yaml").read_text(encoding="utf-8"))


# ------------------------------------------------------------------ AC-020 read


def test_ac020_get_returns_the_active_pack_as_configuration_data(client, db_session) -> None:
    response = client.get(PACK, headers=_headers(db_session, "admin"))

    assert response.status_code == 200
    body = response.json()
    assert body["pack_key"]
    assert body["enabled"] is True
    for section in (
        "code_lists",
        "signals",
        "criteria",
        "counter_evidence",
        "thresholds",
        "workup_items",
        "copy",
    ):
        assert body["config"][section], section
    assert all(item["reasoning"].strip() for item in body["config"]["workup_items"].values())


def test_ac022_get_reports_no_active_pack_when_the_pack_is_disabled(
    client, db_session, monkeypatch
) -> None:
    monkeypatch.setenv("CONDITION_PACK_ENABLED", "false")

    body = client.get(PACK, headers=_headers(db_session, "admin")).json()

    assert body["pack_key"] is None
    assert body["enabled"] is False


# ---------------------------------------------------------------- NFR-019 write


def test_nfr019_put_persists_the_pack_and_the_next_read_serves_it(
    client, db_session, raw: dict
) -> None:
    headers = _headers(db_session, "admin")
    marker = f"marker-{uuid.uuid4().hex[:8]}"
    edited = copy.deepcopy(raw)
    first = next(iter(edited["thresholds"]))
    edited["thresholds"][first] = float(edited["thresholds"][first]) + 0.11
    edited["copy"]["disclaimer"] = marker

    saved = client.put(PACK, headers=headers, json={"config": edited, "change_summary": "edit"})

    assert saved.status_code == 200
    assert saved.json()["version"] > raw["version"]
    assert saved.json()["updated_by"]

    after = client.get(PACK, headers=headers).json()
    assert after["config"]["copy"]["disclaimer"] == marker
    assert after["config"]["thresholds"][first] == pytest.approx(
        float(raw["thresholds"][first]) + 0.11
    )


def test_put_rejects_a_pack_that_fails_schema_validation_naming_the_key(
    client, db_session, raw: dict
) -> None:
    broken = copy.deepcopy(raw)
    del broken["thresholds"]

    response = client.put(PACK, headers=_headers(db_session, "admin"), json={"config": broken})

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert isinstance(detail, list)
    assert "thresholds" in detail[0]["msg"]


# -------------------------------------------------------------- access control


def test_the_pack_routes_are_401_without_a_live_session(client) -> None:
    wrong = {"Authorization": f"Bearer {secrets.token_urlsafe(32)}"}

    assert client.get(PACK, headers=wrong).status_code == 401
    assert client.put(PACK, headers=wrong, json={"config": {}}).status_code == 401


@pytest.mark.parametrize("role", ["patient", "clinician"])
def test_the_pack_routes_are_403_for_a_non_admin_token(client, db_session, role: str) -> None:
    headers = _headers(db_session, role)

    read = client.get(PACK, headers=headers)
    write = client.put(PACK, headers=headers, json={"config": {}})

    assert read.status_code == 403
    assert write.status_code == 403
    assert set(read.json()) == {"detail"}
    assert set(write.json()) == {"detail"}
