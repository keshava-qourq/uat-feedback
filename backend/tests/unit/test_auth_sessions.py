"""Sign-in, sessions, deactivation and password-set tokens (AC-100..AC-104)."""

from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Decision, PasswordSetToken, Patient, User
from app.passwords import issue_password_set_token
from app.security import hash_password


@pytest.fixture
def password() -> str:
    return secrets.token_urlsafe(16)


def _user(db: Session, *, role: str, password: str | None = None, email: str | None = None) -> User:
    user = User(
        email=email or f"{secrets.token_hex(6)}@example.invalid",
        password_hash=hash_password(password) if password else None,
        role=role,
        is_active=True,
        must_set_password=password is None,
    )
    db.add(user)
    db.commit()
    return user


def _login(client: TestClient, email: str, password: str):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_ac100_login_returns_a_token_and_the_acting_account(client, db_session, password):
    user = _user(db_session, role="clinician", password=password)
    response = _login(client, user.email.upper(), password)
    assert response.status_code == 200
    body = response.json()
    assert body["token"]
    assert body["user"] == {
        "id": user.id,
        "email": user.email,
        "role": "clinician",
        "must_set_password": False,
    }

    worklist = client.get("/api/worklist", headers=_headers(body["token"]))
    assert worklist.status_code == 200
    me = client.get("/api/auth/me", headers=_headers(body["token"]))
    assert me.status_code == 200
    assert me.json()["id"] == user.id


def test_ac100_a_wrong_password_and_a_deactivated_account_are_the_same_401(
    client, db_session, password
):
    live = _user(db_session, role="clinician", password=password)
    dead = _user(db_session, role="clinician", password=password)
    dead.is_active = False
    db_session.commit()

    wrong = _login(client, live.email, password + "x")
    deactivated = _login(client, dead.email, password)
    assert wrong.status_code == deactivated.status_code == 401
    assert wrong.json() == deactivated.json() == {"detail": "Invalid credentials"}


def test_ac100_a_recorded_decision_carries_the_signed_in_account(client, db_session, password):
    user = _user(db_session, role="clinician", password=password)
    patient = Patient(dataset_patient_id="P1", dataset_version="v1", display_name="A")
    db_session.add(patient)
    db_session.commit()
    token = _login(client, user.email, password).json()["token"]

    response = client.post(
        f"/api/cases/{patient.id}/decisions",
        json={"decision": "agree", "reason": "looks right"},
        headers=_headers(token),
    )
    assert response.status_code == 201
    assert response.json()["clinician_id"] == user.id
    row = db_session.get(Decision, response.json()["decision_id"])
    assert row.clinician_id == user.id


def test_ac100_an_unknown_decision_value_is_422(client, db_session, password):
    user = _user(db_session, role="clinician", password=password)
    patient = Patient(dataset_patient_id="P2", dataset_version="v1", display_name="B")
    db_session.add(patient)
    db_session.commit()
    token = _login(client, user.email, password).json()["token"]
    response = client.post(
        f"/api/cases/{patient.id}/decisions",
        json={"decision": "maybe"},
        headers=_headers(token),
    )
    assert response.status_code == 422


def test_ac101_logout_revokes_only_the_presented_session(client, db_session, password):
    user = _user(db_session, role="clinician", password=password)
    first = _login(client, user.email, password).json()["token"]
    second = _login(client, user.email, password).json()["token"]

    assert client.post("/api/auth/logout", headers=_headers(first)).status_code == 200
    assert client.get("/api/auth/me", headers=_headers(first)).status_code == 401
    assert client.get("/api/auth/me", headers=_headers(second)).status_code == 200


def test_ac102_an_idle_session_is_401_and_activity_pushes_the_window_forward(
    client, db_session, password, monkeypatch
):
    monkeypatch.setenv("SESSION_IDLE_MINUTES", "15")
    user = _user(db_session, role="clinician", password=password)
    token = _login(client, user.email, password).json()["token"]

    row = db_session.query(__import__("app.models", fromlist=["SessionRow"]).SessionRow).one()
    before = row.idle_expires_at
    assert client.get("/api/auth/me", headers=_headers(token)).status_code == 200
    db_session.refresh(row)
    assert row.idle_expires_at >= before

    row.idle_expires_at = datetime.now(UTC) - timedelta(seconds=1)
    db_session.commit()
    assert client.get("/api/auth/me", headers=_headers(token)).status_code == 401


def test_ac103_deactivation_revokes_every_session_and_blocks_later_logins(
    client, db_session, password
):
    admin = _user(db_session, role="admin", password=password)
    victim = _user(db_session, role="clinician", password=password)
    admin_token = _login(client, admin.email, password).json()["token"]
    one = _login(client, victim.email, password).json()["token"]
    two = _login(client, victim.email, password).json()["token"]

    response = client.post(
        f"/api/admin/users/{victim.id}/deactivate", headers=_headers(admin_token)
    )
    assert response.status_code == 200
    assert response.json() == {"id": victim.id, "is_active": False, "sessions_revoked": 2}
    assert client.get("/api/auth/me", headers=_headers(one)).status_code == 401
    assert client.get("/api/auth/me", headers=_headers(two)).status_code == 401
    assert _login(client, victim.email, password).json() == {"detail": "Invalid credentials"}


def test_ac103_deactivate_is_401_unauthenticated_403_non_admin_and_404_unknown(
    client, db_session, password
):
    clinician = _user(db_session, role="clinician", password=password)
    admin = _user(db_session, role="admin", password=password)
    target = _user(db_session, role="clinician", password=password)

    assert client.post(f"/api/admin/users/{target.id}/deactivate").status_code == 401
    clinician_token = _login(client, clinician.email, password).json()["token"]
    assert (
        client.post(
            f"/api/admin/users/{target.id}/deactivate", headers=_headers(clinician_token)
        ).status_code
        == 403
    )
    admin_token = _login(client, admin.email, password).json()["token"]
    assert (
        client.post(
            "/api/admin/users/does-not-exist/deactivate", headers=_headers(admin_token)
        ).status_code
        == 404
    )


def test_ac104_an_admin_created_account_has_no_password_and_one_set_password_token(
    client, db_session, password
):
    admin = _user(db_session, role="admin", password=password)
    admin_token = _login(client, admin.email, password).json()["token"]
    email = f"{secrets.token_hex(6)}@example.invalid"

    created = client.post(
        "/api/admin/users",
        json={"email": email, "role": "clinician"},
        headers=_headers(admin_token),
    )
    assert created.status_code == 201
    body = created.json()
    assert body["email"] == email
    assert body["role"] == "clinician"
    assert body["must_set_password"] is True
    assert "password" not in body and "password_hash" not in body

    new_user = db_session.get(User, body["id"])
    assert new_user.password_hash is None
    assert _login(client, email, password).status_code == 401

    token = body["set_password_token"]
    stored = (
        db_session.query(PasswordSetToken).filter(PasswordSetToken.user_id == new_user.id).one()
    )
    assert stored.token_hash != token
    assert (
        client.post(
            "/api/auth/set-password", json={"token": token, "new_password": password}
        ).status_code
        == 200
    )
    assert _login(client, email, password).status_code == 200


def test_ac104_creating_a_user_is_401_unauthenticated_and_403_for_a_clinician(
    client, db_session, password
):
    clinician = _user(db_session, role="clinician", password=password)
    payload = {"email": f"{secrets.token_hex(6)}@example.invalid", "role": "clinician"}

    assert client.post("/api/admin/users", json=payload).status_code == 401
    token = _login(client, clinician.email, password).json()["token"]
    assert client.post("/api/admin/users", json=payload, headers=_headers(token)).status_code == 403


def test_ac104_an_invited_account_cannot_log_in_until_it_sets_a_password(
    client, db_session, password
):
    user = _user(db_session, role="clinician")
    assert user.password_hash is None
    assert user.must_set_password is True
    assert _login(client, user.email, password).status_code == 401

    token = issue_password_set_token(db_session, user)
    stored = db_session.query(PasswordSetToken).one()
    assert token not in (stored.token_hash, "")
    assert stored.token_hash != token

    response = client.post(
        "/api/auth/set-password", json={"token": token, "new_password": password}
    )
    assert response.status_code == 200
    assert response.json() == {"detail": "password set"}

    db_session.refresh(user)
    assert user.must_set_password is False
    assert user.password_hash.startswith("$2")
    assert password not in user.password_hash
    assert _login(client, user.email, password).status_code == 200


def test_ac104_a_set_password_token_is_single_use_expiring_and_unknown_is_404(
    client, db_session, password
):
    user = _user(db_session, role="clinician")
    token = issue_password_set_token(db_session, user)
    assert (
        client.post(
            "/api/auth/set-password", json={"token": token, "new_password": password}
        ).status_code
        == 200
    )
    # consumed
    assert (
        client.post(
            "/api/auth/set-password", json={"token": token, "new_password": password}
        ).status_code
        == 409
    )
    # expired
    other = _user(db_session, role="clinician")
    expired = issue_password_set_token(db_session, other)
    row = db_session.query(PasswordSetToken).filter(PasswordSetToken.user_id == other.id).one()
    row.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    db_session.commit()
    assert (
        client.post(
            "/api/auth/set-password", json={"token": expired, "new_password": password}
        ).status_code
        == 409
    )
    # revoked
    third = _user(db_session, role="clinician")
    revoked = issue_password_set_token(db_session, third)
    revoked_row = (
        db_session.query(PasswordSetToken).filter(PasswordSetToken.user_id == third.id).one()
    )
    revoked_row.revoked_at = datetime.now(UTC)
    db_session.commit()
    assert (
        client.post(
            "/api/auth/set-password", json={"token": revoked, "new_password": password}
        ).status_code
        == 409
    )
    # unknown
    assert (
        client.post(
            "/api/auth/set-password",
            json={"token": secrets.token_urlsafe(32), "new_password": password},
        ).status_code
        == 404
    )
