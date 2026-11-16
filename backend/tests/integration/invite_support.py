"""Helpers for the patient-invite lifecycle tests (US-026-3).

Everything a test needs -- a cohort of patients, a clinician account, a
patient-role session -- is built by calling the real API: the cohort is read
from GET /api/worklist (an ingest run is started only when the environment has
no cohort at all, because NFR-021 serialises ingest and the sandbox database is
shared), the clinician comes from the admin user route plus set-password, and
the patient session from issue-and-accept. No row is ever written by hand, and
every clinician and invite is created per test so concurrent tests never share
a token.
"""

from __future__ import annotations

import os
import secrets
import uuid
from typing import Any
from urllib.parse import urlsplit

from fastapi.testclient import TestClient

from tests.integration import fixtures_dataset as fx
from tests.integration.conftest import wait_for_run
from tests.integration.fixtures_provenance import ProvenanceDrop

INVITES = "/api/invites"
ADMIN_USERS = "/api/admin/users"
LOGIN = "/api/auth/login"
SET_PASSWORD = "/api/auth/set-password"

#: Where a one-time password-set token may arrive in the create-user response.
TOKEN_KEYS = (
    "set_password_token",
    "password_set_token",
    "password_token",
    "invite_token",
    "token",
)

#: Where the invite's tokenised link may arrive in the issue response.
LINK_KEYS = ("link", "invite_link", "url", "invite_url")


def new_password() -> str:
    return secrets.token_urlsafe(24)


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


def strings(payload: Any) -> list[str]:
    if isinstance(payload, str):
        return [payload]
    if isinstance(payload, dict):
        out: list[str] = []
        for key, value in payload.items():
            out.append(str(key))
            out.extend(strings(value))
        return out
    if isinstance(payload, list):
        out = []
        for item in payload:
            out.extend(strings(item))
        return out
    return [] if payload is None else [str(payload)]


def find(payload: Any, keys: tuple[str, ...]) -> str | None:
    for obj in objects(payload):
        for key in keys:
            value = obj.get(key)
            if isinstance(value, str) and value.strip():
                return value
    return None


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def drain_ingest_queue() -> None:
    """Run whatever is on the ingest queue, as the deployed RQ worker would."""
    import redis
    from rq import Queue, SimpleWorker

    connection = redis.from_url(os.environ["REDIS_URL"])
    queue = Queue("ingest", connection=connection)
    SimpleWorker([queue], connection=connection).work(burst=True)


#: The cohort these tests share. Ingest is deliberately serialised one run at a
#: time (NFR-021), so a run per test would spend the suite colliding with 409s:
#: the cohort is built once for the module and every test takes its own patient
#: and its own freshly issued invite out of it.
_COHORT: dict[str, str] = {}

INGEST_START = "/api/admin/ingest-runs"


def _worklist_rows(api: TestClient, admin: dict[str, str]) -> list[dict]:
    response = api.get("/api/worklist", headers=admin)
    assert response.status_code == 200, (
        f"GET /api/worklist returned {response.status_code}: {response.text[:200]}"
    )
    return [
        row
        for row in objects(response.json())
        if row.get("patient_id") and row.get("dataset_patient_id")
    ]


def _cohort_from_worklist(api: TestClient, admin: dict[str, str]) -> dict[str, str]:
    """The cohort already loaded in this environment, newest invite state last.

    Patients nobody has invited yet come first, so each test starts from a row
    whose invite status is the one its own freshly issued invite sets.
    """
    rows = _worklist_rows(api, admin)
    uninvited = [
        row for row in rows if str(row.get("invite_status") or "none").lower() == "none"
    ]
    chosen = uninvited if len(uninvited) >= 2 else rows
    return {
        str(row["dataset_patient_id"]): str(row["patient_id"]) for row in chosen
    }


def _try_ingest(api: TestClient, admin: dict[str, str]) -> None:
    """Load one small cohort, but only when the environment has none.

    Ingest is serialised one run at a time (NFR-021) and the sandbox database is
    shared, so a 409 here is the backend behaving: another run is in flight and
    will leave a cohort behind. Drain the queue as the deployed worker would and
    give up rather than block the suite -- the caller re-reads the worklist.
    """
    drop = ProvenanceDrop(uuid.uuid4().hex[:8])
    source_uri, _prefix = fx.upload_fixture_set(drop.files())
    response = api.post(
        INGEST_START,
        headers=admin,
        json={
            "dataset_version": f"qa-invite-{drop.suffix}",
            "source_uri": source_uri,
            "seed": 23,
        },
    )
    drain_ingest_queue()
    if response.status_code == 409:
        return
    assert response.status_code in (200, 202), (
        f"starting the cohort's ingest run returned {response.status_code}: "
        f"{response.text[:300]}"
    )
    wait_for_run(api, admin, response.json()["run_id"])


def ingest_cohort(api: TestClient, admin: dict[str, str]) -> dict[str, str]:
    """The patient cohort these invite tests use: whatever the real API already
    serves on GET /api/worklist, ingesting one small drop only when there is
    none. Returns dataset patient id -> internal patient uuid."""
    if len(_COHORT) >= 2:
        return dict(_COHORT)

    found = _cohort_from_worklist(api, admin)
    if len(found) < 2:
        _try_ingest(api, admin)
        found = _cohort_from_worklist(api, admin)

    assert len(found) >= 2, (
        "no cohort of at least two patients is visible through GET /api/worklist, so "
        f"no patient can be invited: found {sorted(found)}"
    )
    _COHORT.update(found)
    return dict(found)


def two_patient_ids(api: TestClient, admin: dict[str, str]) -> tuple[str, str]:
    """Two distinct patient uuids from the module's cohort."""
    ids = sorted(ingest_cohort(api, admin).values())
    return ids[0], ids[1]


def sign_in_clinician(api: TestClient, admin: dict[str, str]) -> str:
    """A brand new clinician, created and signed in through the real API.

    Returns their session token.
    """
    email = f"qa-inv-clin-{uuid.uuid4().hex[:10]}@example.test"
    created = api.post(ADMIN_USERS, headers=admin, json={"email": email, "role": "clinician"})
    assert created.status_code in (200, 201), (
        f"POST {ADMIN_USERS} returned {created.status_code}: {created.text[:300]}"
    )
    token = find(created.json(), TOKEN_KEYS)
    assert token, (
        "creating a clinician answered no one-time password-set token, so the account "
        f"can never be used: {created.text[:300]}"
    )
    password = new_password()
    done = api.post(SET_PASSWORD, json={"token": token, "password": password})
    assert done.status_code in (200, 204), (
        f"POST {SET_PASSWORD} returned {done.status_code}: {done.text[:300]}"
    )
    signed_in = api.post(LOGIN, json={"email": email, "password": password})
    assert signed_in.status_code == 200, (
        f"the new clinician cannot sign in: {signed_in.status_code} {signed_in.text[:300]}"
    )
    return str(signed_in.json()["token"])


def issue_invite(
    api: TestClient,
    clinician: dict[str, str],
    patient_id: str,
    *,
    expires_in_hours: int = 72,
    expect: tuple[int, ...] = (200, 201),
) -> Any:
    return api.post(
        INVITES,
        headers=clinician,
        json={
            "patient_id": patient_id,
            "expires_in_hours": expires_in_hours,
            "send_email": False,
        },
    ), expect


def issued(api: TestClient, clinician: dict[str, str], patient_id: str, **kwargs: Any) -> dict:
    """Issue one invite and return its body; fails the criterion if it is refused."""
    response, expect = issue_invite(api, clinician, patient_id, **kwargs)
    assert response.status_code in expect, (
        f"POST {INVITES} for patient {patient_id} returned {response.status_code}: "
        f"{response.text[:300]}"
    )
    return response.json()


def token_of(body: dict) -> str:
    """The single-use token carried by an issue response's tokenised link."""
    link = find(body, LINK_KEYS)
    assert link, f"the issued invite carries no tokenised link: {str(body)[:300]}"
    path = urlsplit(link).path or link
    token = [part for part in path.split("/") if part][-1]
    assert token, f"the invite link carries no token: {link!r}"
    return token


def accept(api: TestClient, token: str, password: str | None = None) -> Any:
    body = {"new_password": password} if password else {}
    return api.post(f"{INVITES}/{token}/accept", json=body)


def patient_session(api: TestClient, token: str) -> str:
    """Accept an invite and return the patient-role session token it hands back."""
    response = accept(api, token)
    assert response.status_code == 200, (
        f"POST {INVITES}/{{token}}/accept returned {response.status_code}: "
        f"{response.text[:300]}"
    )
    session = find(response.json(), ("token", "session_token", "access_token"))
    assert session, f"accepting the invite answered no session token: {response.text[:300]}"
    return session
