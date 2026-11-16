"""US-026: issuing, opening, accepting and scoping single-use patient invites."""

from __future__ import annotations

import secrets
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from app.invites import DEFAULT_EXPIRY_HOURS, expiry
from app.models import IntakeAnswer, Invite, Patient, User
from app.security import hash_password
from app.sessions import hash_token, issue_session


def password() -> str:
    return secrets.token_urlsafe(16)


@pytest.fixture
def patient(db_session: Session) -> Patient:
    row = Patient(
        dataset_patient_id=f"P{uuid.uuid4().hex[:8]}",
        dataset_version="v1",
        display_name="Robin Fields",
    )
    db_session.add(row)
    db_session.commit()
    return row


def _staff(db_session: Session, role: str = "clinician") -> str:
    user = User(
        email=f"{role}-{uuid.uuid4().hex}@example.invalid",
        password_hash=hash_password(password()),
        role=role,
        is_active=True,
        must_set_password=False,
    )
    db_session.add(user)
    db_session.commit()
    return issue_session(db_session, user)


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _issue(client, db_session, patient_id: str, role: str = "clinician"):
    return client.post(
        "/api/invites",
        json={"patient_id": patient_id},
        headers=_headers(_staff(db_session, role)),
    )


# ------------------------------------------------------------------ AC-084


def test_ac084_issuing_returns_the_invite_and_its_url_once(client, db_session, patient):
    response = _issue(client, db_session, patient.id)
    assert response.status_code == 201
    body = response.json()
    assert body["patient_id"] == patient.id
    assert body["status"] == "issued"
    assert body["token"] in body["invite_url"]
    expires = datetime.fromisoformat(body["expires_at"])
    assert expires.utcoffset() == timedelta(0)
    assert expires > datetime.now(UTC)
    assert uuid.UUID(body["invite_id"])


def test_ac084_an_admin_may_issue_and_a_patient_token_is_403(client, db_session, patient):
    assert _issue(client, db_session, patient.id, "admin").status_code == 201
    assert _issue(client, db_session, patient.id, "patient").status_code == 403


def test_ac084_an_unknown_patient_is_404_and_a_missing_patient_id_is_422(
    client, db_session, patient
):
    assert _issue(client, db_session, str(uuid.uuid4())).status_code == 404
    response = client.post(
        "/api/invites", json={}, headers=_headers(_staff(db_session, "clinician"))
    )
    assert response.status_code == 422


# ------------------------------------------------------------------ AC-086


def test_ac086_nfr009_the_token_is_unguessable_not_a_uuid_and_stored_only_hashed(
    client, db_session, patient
):
    token = _issue(client, db_session, patient.id).json()["token"]
    assert len(token) >= 32
    with pytest.raises(ValueError):
        uuid.UUID(token)
    row = db_session.query(Invite).one()
    assert row.token_hash != token
    assert row.token_hash == hash_token(token)
    assert row.granted_role == "patient"
    assert row.patient_id == patient.id


def test_ac086_nfr009_the_expiry_comes_from_invite_expiry_hours(monkeypatch):
    monkeypatch.setenv("INVITE_EXPIRY_HOURS", "5")
    assert expiry() == timedelta(hours=5)
    monkeypatch.delenv("INVITE_EXPIRY_HOURS")
    assert expiry() == timedelta(hours=DEFAULT_EXPIRY_HOURS)


# ------------------------------------------------------------------ open


def test_ac085_opening_the_link_is_unauthenticated_and_records_the_open(
    client, db_session, patient
):
    token = _issue(client, db_session, patient.id).json()["token"]
    first = client.get(f"/api/invites/{token}")
    assert first.status_code == 200
    assert first.json()["patient_display_name"] == "Robin Fields"
    assert first.json()["status"] == "not_yet_opened"
    assert client.get(f"/api/invites/{token}").json()["status"] == "opened"


def test_an_unknown_token_is_404_and_an_expired_one_is_409(client, db_session, patient):
    assert client.get(f"/api/invites/{secrets.token_urlsafe(32)}").status_code == 404
    token = _issue(client, db_session, patient.id).json()["token"]
    row = db_session.query(Invite).one()
    row.expires_at = datetime.now(UTC) - timedelta(hours=1)
    db_session.commit()
    expired = client.get(f"/api/invites/{token}")
    assert expired.status_code == 409
    assert client.post(f"/api/invites/{token}/accept", json={"password": password()}).json() == (
        expired.json()
    )


# ------------------------------------------------------------------ accept


def test_accepting_creates_the_patient_user_and_returns_a_session(client, db_session, patient):
    token = _issue(client, db_session, patient.id).json()["token"]
    response = client.post(f"/api/invites/{token}/accept", json={"password": password()})
    assert response.status_code == 200
    body = response.json()
    assert body["user"]["role"] == "patient"
    assert body["user"]["must_set_password"] is False
    user = db_session.get(User, body["user"]["id"])
    assert user.patient_id == patient.id
    assert client.get("/api/auth/me", headers=_headers(body["token"])).status_code == 200


def test_nfr009_an_invite_is_single_use_and_re_use_is_409(client, db_session, patient):
    token = _issue(client, db_session, patient.id).json()["token"]
    first = client.post(f"/api/invites/{token}/accept", json={"password": password()})
    assert first.status_code == 200
    again = client.post(f"/api/invites/{token}/accept", json={"password": password()})
    assert again.status_code == 409
    assert client.get(f"/api/invites/{token}").status_code == 409


def test_nfr009_the_session_grants_patient_access_only_to_that_patient(client, db_session, patient):
    token = _issue(client, db_session, patient.id).json()["token"]
    session = client.post(f"/api/invites/{token}/accept", json={"password": password()}).json()[
        "token"
    ]
    assert client.get("/api/worklist", headers=_headers(session)).status_code == 403
    mine = client.get("/api/patients/me/timeline", headers=_headers(session))
    assert mine.status_code == 200
    assert mine.json()["patient_id"] in (patient.id, None)


def test_accepting_an_unknown_token_is_404(client):
    response = client.post(
        f"/api/invites/{secrets.token_urlsafe(32)}/accept", json={"password": password()}
    )
    assert response.status_code == 404


# ------------------------------------------------------------------ AC-085


def test_ac085_the_worklist_carries_the_invite_status_through_its_states(
    client, db_session, patient
):
    staff = _headers(_staff(db_session, "clinician"))

    def status_now() -> str:
        items = client.get("/api/worklist", headers=staff).json()["items"]
        return next(item["invite_status"] for item in items if item["patient_id"] == patient.id)

    assert status_now() == "none"
    token = _issue(client, db_session, patient.id).json()["token"]
    assert status_now() == "not_yet_opened"
    client.get(f"/api/invites/{token}")
    assert status_now() == "opened"
    db_session.add(
        IntakeAnswer(
            patient_id=patient.id,
            question_key="night_pain",
            answer_value=True,
            answered_at=datetime.now(UTC),
            is_complete=True,
        )
    )
    db_session.commit()
    assert status_now() == "intake_completed"


def test_ac085_the_intake_can_be_completed_and_the_worklist_follows(client, db_session, patient):
    token = _issue(client, db_session, patient.id).json()["token"]
    session = _headers(
        client.post(f"/api/invites/{token}/accept", json={"password": password()}).json()["token"]
    )
    for _ in range(20):
        question = client.get("/api/patients/me/intake", headers=session).json()["next_question"]
        if question is None:
            break
        answered = client.post(
            "/api/patients/me/intake/answers",
            headers=session,
            json={"question_key": question["key"], "answer_value": "yes"},
        )
        assert answered.status_code == 200
    assert client.get("/api/patients/me/intake", headers=session).json()["complete"] is True

    staff = _headers(_staff(db_session, "clinician"))
    items = client.get("/api/worklist", headers=staff).json()["items"]
    row = next(item for item in items if item["patient_id"] == patient.id)
    assert row["invite_status"] == "intake_completed"


def test_nfr009_a_revoked_invite_is_refused_like_a_consumed_one(client, db_session, patient):
    staff = _headers(_staff(db_session, "clinician"))
    body = client.post("/api/invites", json={"patient_id": patient.id}, headers=staff).json()
    assert client.delete(f"/api/invites/{body['invite_id']}", headers=staff).status_code == 204
    refused = client.post(f"/api/invites/{body['token']}/accept", json={"password": password()})
    assert refused.status_code == 409
    assert set(refused.json()) == {"detail"}


def test_nfr009_an_invite_issued_with_a_zero_hour_expiry_is_already_expired(
    client, db_session, patient
):
    staff = _headers(_staff(db_session, "clinician"))
    body = client.post(
        "/api/invites",
        json={"patient_id": patient.id, "expires_in_hours": 0},
        headers=staff,
    ).json()
    assert client.get(f"/api/invites/{body['token']}").status_code == 409


def test_invite_listings_are_newest_first_by_creation_time(client, db_session, patient):
    from app.invites import _latest_invite

    older = _issue(client, db_session, patient.id).json()["invite_id"]
    newer = _issue(client, db_session, patient.id).json()["invite_id"]
    db_session.get(Invite, older).created_at = datetime.now(UTC) - timedelta(hours=2)
    db_session.commit()
    assert _latest_invite(db_session, patient.id).id == newer
