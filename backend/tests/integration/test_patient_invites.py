"""US-026-3: the patient invite lifecycle and its security properties, proved
against the real API (AC-084, AC-085, AC-086, NFR-009).

Everything goes through the real HTTP API against the sandbox's PostgreSQL and
Redis: the bootstrap admin signs in through POST /api/auth/login, the cohort
comes from an ingest run started through POST /api/admin/ingest-runs, the
clinician is created through the admin route and signs in, and every patient
session is obtained by issuing and accepting an invite. No row is written by
hand and each test issues its own invite and patient, so concurrent tests never
share a token or a patient.
"""

from __future__ import annotations

import re
import uuid

from fastapi.testclient import TestClient

from tests.integration.conftest import admin_headers
from tests.integration.invite_support import (
    INVITES,
    accept,
    bearer,
    find,
    issue_invite,
    issued,
    new_password,
    objects,
    patient_session,
    sign_in_clinician,
    strings,
    token_of,
    two_patient_ids,
)

UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE
)

#: The three readings AC-085 fixes for the worklist's invite status, and the
#: spellings the data model allows for each (`not_opened` in the column,
#: "not yet opened" on screen).
NOT_YET_OPENED = {"not_yet_opened", "not_opened", "not yet opened", "issued", "pending"}
OPENED = {"opened"}
INTAKE_COMPLETED = {"intake_completed", "intake completed", "completed"}

#: Routes a patient-role session must never reach (clinician and admin).
STAFF_ROUTES = (
    ("GET", "/api/worklist"),
    ("GET", "/api/admin/settings"),
    ("GET", "/api/admin/pack"),
)


def _clinician(api: TestClient) -> tuple[dict[str, str], dict[str, str], str, str]:
    """(admin headers, clinician headers, patient_id, other patient_id)."""
    admin = admin_headers(api)
    clinician = bearer(sign_in_clinician(api, admin))
    patient_id, other_id = two_patient_ids(api, admin)
    return admin, clinician, patient_id, other_id


def _worklist_row(api: TestClient, headers: dict[str, str], patient_id: str) -> dict:
    response = api.get("/api/worklist", headers=headers)
    assert response.status_code == 200, (
        f"GET /api/worklist returned {response.status_code}: {response.text[:200]}"
    )
    rows = [row for row in objects(response.json()) if str(row.get("patient_id")) == patient_id]
    assert rows, f"patient {patient_id} has no worklist row: {response.text[:300]}"
    return rows[0]


def _invite_status(row: dict) -> str:
    value = row.get("invite_status")
    assert value is not None, f"the worklist row reports no invite_status: {str(row)[:300]}"
    return str(value).strip().lower()


# ------------------------------------------------------------------------ AC-084


def test_ac084_a_clinician_issues_an_invite_and_is_shown_a_tokenised_link(
    api: TestClient,
) -> None:
    """AC-084: a signed-in clinician issues an invite for one patient and the
    response carries a single-use tokenised link with its expiry and status."""
    _admin, clinician, patient_id, _other = _clinician(api)

    body = issued(api, clinician, patient_id)
    assert body.get("invite_id"), f"the issued invite has no invite_id: {str(body)[:300]}"
    assert body.get("expires_at"), f"the issued invite has no expiry: {str(body)[:300]}"
    assert body.get("status"), f"the issued invite has no status: {str(body)[:300]}"

    token = token_of(body)
    opened = api.get(f"{INVITES}/{token}")
    assert opened.status_code == 200, (
        f"the link just issued does not resolve: GET {INVITES}/{{token}} returned "
        f"{opened.status_code}: {opened.text[:300]}"
    )
    assert opened.json().get("valid") is True, (
        f"the link just issued is not reported valid: {opened.text[:300]}"
    )


def test_ac084_issuing_twice_yields_two_distinct_single_use_tokens(api: TestClient) -> None:
    """AC-084: issuing an invite twice for the same patient yields two different
    tokens, and each one is single-use -- accepting a token a second time is 409."""
    _admin, clinician, patient_id, _other = _clinician(api)

    first = token_of(issued(api, clinician, patient_id))
    second = token_of(issued(api, clinician, patient_id))
    assert first != second, "issuing an invite twice returned the same token"

    accepted = accept(api, first, new_password())
    assert accepted.status_code == 200, (
        f"accepting a fresh invite returned {accepted.status_code}: {accepted.text[:300]}"
    )
    again = accept(api, first, new_password())
    assert again.status_code == 409, (
        f"re-using a consumed invite token returned {again.status_code}; a single-use "
        f"token must be refused: {again.text[:300]}"
    )
    assert set(again.json()) == {"detail"}


# ------------------------------------------------------------------------ AC-085


def test_ac085_the_worklist_row_reports_not_yet_opened_then_opened(api: TestClient) -> None:
    """AC-085: the patient's worklist row reads 'not yet opened' after the invite is
    issued and 'opened' once GET /api/invites/{token} has been called."""
    _admin, clinician, patient_id, _other = _clinician(api)
    token = token_of(issued(api, clinician, patient_id))

    before = _invite_status(_worklist_row(api, clinician, patient_id))
    assert before in NOT_YET_OPENED, (
        f"a freshly issued invite reads {before!r} on the worklist; it must read "
        "'not yet opened'"
    )

    visited = api.get(f"{INVITES}/{token}")
    assert visited.status_code == 200, (
        f"GET {INVITES}/{{token}} returned {visited.status_code}: {visited.text[:300]}"
    )

    after = _invite_status(_worklist_row(api, clinician, patient_id))
    assert after in OPENED, (
        f"after the patient opened the link the worklist still reads {after!r}; it "
        "must read 'opened'"
    )


def test_ac085_the_worklist_row_reports_intake_completed_once_intake_is_complete(
    api: TestClient,
) -> None:
    """AC-085: once the invited patient has completed the intake, the clinician's
    worklist row for that patient reads 'intake completed'."""
    _admin, clinician, patient_id, _other = _clinician(api)
    token = token_of(issued(api, clinician, patient_id))
    assert api.get(f"{INVITES}/{token}").status_code == 200
    patient = bearer(patient_session(api, token))

    for _ in range(100):
        state = api.get("/api/patients/me/intake", headers=patient)
        assert state.status_code == 200, (
            f"GET /api/patients/me/intake returned {state.status_code}: {state.text[:300]}"
        )
        question = state.json().get("next_question")
        if not question:
            break
        answered = api.post(
            "/api/patients/me/intake/answers",
            headers=patient,
            json={"question_key": question["key"], "answer_value": "yes"},
        )
        assert answered.status_code == 200, (
            f"answering intake question {question['key']!r} returned "
            f"{answered.status_code}: {answered.text[:300]}"
        )
    else:  # pragma: no cover - a never-ending intake is itself the failure
        raise AssertionError("the intake never reported itself complete after 100 answers")

    status = _invite_status(_worklist_row(api, clinician, patient_id))
    assert status in INTAKE_COMPLETED, (
        f"after the patient completed the intake the worklist reads {status!r}; it must "
        "read 'intake completed'"
    )


# -------------------------------------------------------------- AC-086 / NFR-009


def test_ac086_nfr009_the_token_is_long_random_and_not_a_uuid(api: TestClient) -> None:
    """AC-086 / NFR-009: the invite token is an opaque random string, not a UUID,
    long enough to be unguessable, and two tokens share no structure."""
    _admin, clinician, patient_id, _other = _clinician(api)

    tokens = [token_of(issued(api, clinician, patient_id)) for _ in range(3)]
    for token in tokens:
        assert not UUID_PATTERN.match(token), (
            f"the invite token is a UUID ({token[:8]}...), which is guessable from the "
            "data model's own identifiers"
        )
        assert len(token) >= 24, (
            f"the invite token is only {len(token)} characters long; an unguessable "
            "token needs substantially more entropy"
        )
    assert len(set(tokens)) == 3, "three invites issued fewer than three distinct tokens"
    assert len({token[:8] for token in tokens}) == 3, (
        f"the invite tokens share a fixed prefix, so they are not random: {tokens}"
    )


def test_ac086_nfr009_no_endpoint_returns_or_lists_a_live_token_again(api: TestClient) -> None:
    """AC-086 / NFR-009: once issued, the token value is never handed back -- not by
    the worklist, not by the case view, not by validating the link itself."""
    _admin, clinician, patient_id, _other = _clinician(api)
    admin = admin_headers(api)
    token = token_of(issued(api, clinician, patient_id))

    leaking: list[str] = []
    paths = [
        ("GET", "/api/worklist", clinician),
        ("GET", INVITES, clinician),
        ("GET", f"{INVITES}/{token}", {}),
        ("GET", f"/api/cases/{patient_id}", clinician),
        ("GET", f"/api/cases/{patient_id}/timeline", clinician),
        ("GET", "/api/admin/settings", admin),
    ]
    for method, path, headers in paths:
        response = api.request(method, path, headers=headers or None)
        if response.status_code != 200:
            continue
        if token in set(strings(response.json())) or token in response.text:
            leaking.append(f"{method} {path}")
    assert not leaking, f"these responses hand back the live invite token: {leaking}"


def test_ac086_nfr009_expired_accepted_and_revoked_are_refused_the_same_way(
    api: TestClient,
) -> None:
    """AC-086 / NFR-009: an invite past its expiry, one already accepted and one
    revoked are each refused with 409 and with the same body, so which of the three
    states caused the refusal cannot be told apart."""
    _admin, clinician, patient_id, other_id = _clinician(api)

    # 1. past its configured expiry
    expired_response, _ = issue_invite(api, clinician, patient_id, expires_in_hours=0)
    assert expired_response.status_code in (200, 201), (
        "an invite cannot be issued with a zero-hour expiry, so an expired invite "
        f"cannot be exercised: {expired_response.status_code} {expired_response.text[:300]}"
    )
    expired_token = token_of(expired_response.json())

    # 2. already accepted
    accepted_token = token_of(issued(api, clinician, patient_id))
    assert accept(api, accepted_token, new_password()).status_code == 200

    # 3. revoked by the clinician who issued it
    revoked_body = issued(api, clinician, other_id)
    revoked_token = token_of(revoked_body)
    invite_id = revoked_body.get("invite_id")
    revoked = api.request("DELETE", f"{INVITES}/{invite_id}", headers=clinician)
    if revoked.status_code in (404, 405):
        revoked = api.post(f"{INVITES}/{invite_id}/revoke", headers=clinician)
    assert revoked.status_code in (200, 204), (
        "an issued invite cannot be revoked through the API (tried DELETE "
        f"{INVITES}/{{invite_id}} and POST {INVITES}/{{invite_id}}/revoke), so NFR-009's "
        f"revocability is not met: {revoked.status_code} {revoked.text[:300]}"
    )

    bodies: dict[str, object] = {}
    for name, token in (
        ("expired", expired_token),
        ("accepted", accepted_token),
        ("revoked", revoked_token),
    ):
        response = accept(api, token, new_password())
        assert response.status_code == 409, (
            f"accepting an {name} invite returned {response.status_code}; it must be "
            f"refused with 409: {response.text[:300]}"
        )
        assert set(response.json()) == {"detail"}
        bodies[name] = response.json()

    assert len({str(body) for body in bodies.values()}) == 1, (
        "the three refusals answer different bodies, so expired, accepted and revoked "
        f"can be told apart: {bodies}"
    )


def test_ac086_nfr009_an_accepted_session_reaches_only_that_patients_own_data(
    api: TestClient,
) -> None:
    """AC-086 / NFR-009: the session POST /api/invites/{token}/accept returns is
    patient-role and scoped to the one patient -- it reads that patient's own data,
    is 403 on clinician and admin routes, and 404/403 on another patient's data."""
    _admin, clinician, patient_id, other_id = _clinician(api)
    token = token_of(issued(api, clinician, patient_id))
    accepted = accept(api, token, new_password())
    assert accepted.status_code == 200, (
        f"accepting a fresh invite returned {accepted.status_code}: {accepted.text[:300]}"
    )
    body = accepted.json()
    session = find(body, ("token", "session_token", "access_token"))
    assert session, f"accepting the invite answered no session token: {accepted.text[:300]}"
    user = body.get("user") or {}
    assert str(user.get("role")) == "patient", (
        f"the invite granted role {user.get('role')!r} rather than patient: {str(body)[:300]}"
    )
    assert str(user.get("patient_id")) == patient_id, (
        f"the invite's session is scoped to patient {user.get('patient_id')!r}, not to "
        f"the invited patient {patient_id}"
    )
    headers = bearer(session)

    own = api.get("/api/patients/me/timeline", headers=headers)
    assert own.status_code == 200, (
        f"the invited patient cannot read their own timeline: {own.status_code} "
        f"{own.text[:300]}"
    )

    refused = []
    for method, path in STAFF_ROUTES:
        response = api.request(method, path, headers=headers)
        if response.status_code != 403:
            refused.append((f"{method} {path}", response.status_code))
        else:
            assert set(response.json()) == {"detail"}
    assert not refused, (
        f"a patient-role invite session reached these staff routes with something "
        f"other than 403: {refused}"
    )

    for path in (f"/api/cases/{other_id}", f"/api/cases/{other_id}/timeline"):
        response = api.get(path, headers=headers)
        assert response.status_code in (403, 404), (
            f"GET {path} with another patient's invite session returned "
            f"{response.status_code}: an invite grants access to one patient only"
        )
        assert set(response.json()) == {"detail"}


def test_ac086_an_unknown_invite_token_is_404(api: TestClient) -> None:
    """AC-086 / behaviour rules: a token that belongs to no invite is not found,
    on both the validate and the accept route."""
    unknown = uuid.uuid4().hex + uuid.uuid4().hex

    validated = api.get(f"{INVITES}/{unknown}")
    assert validated.status_code == 404, (
        f"GET {INVITES}/{{unknown token}} returned {validated.status_code}: "
        f"{validated.text[:200]}"
    )
    assert set(validated.json()) == {"detail"}

    accepted = accept(api, unknown, new_password())
    assert accepted.status_code == 404, (
        f"accepting an unknown invite token returned {accepted.status_code}: "
        f"{accepted.text[:200]}"
    )
    assert set(accepted.json()) == {"detail"}


# ----------------------------------------------------- who may issue an invite


def test_ac086_a_patient_token_cannot_issue_an_invite(api: TestClient) -> None:
    """Behaviour rules: an authenticated token of the wrong role is 403 -- a patient
    session obtained from an invite may not issue invites of its own."""
    _admin, clinician, patient_id, other_id = _clinician(api)
    token = token_of(issued(api, clinician, patient_id))
    patient = bearer(patient_session(api, token))

    response, _ = issue_invite(api, patient, other_id)
    assert response.status_code == 403, (
        f"POST {INVITES} with a patient-role token returned {response.status_code}: "
        f"{response.text[:300]}"
    )
    assert set(response.json()) == {"detail"}


def test_ac086_an_unauthenticated_issue_is_401(api: TestClient) -> None:
    """Behaviour rules: no bearer token means 401, with the one error shape."""
    response = api.post(
        INVITES,
        json={"patient_id": str(uuid.uuid4()), "expires_in_hours": 72, "send_email": False},
    )

    assert response.status_code == 401, (
        f"POST {INVITES} unauthenticated returned {response.status_code}: "
        f"{response.text[:200]}"
    )
    assert set(response.json()) == {"detail"}


def test_ac084_issuing_an_invite_for_an_unknown_patient_is_404(api: TestClient) -> None:
    """AC-084 / behaviour rules: an invite is scoped to one real patient, so an
    unknown patient id is not found."""
    _admin, clinician, _patient_id, _other = _clinician(api)

    response, _ = issue_invite(api, clinician, str(uuid.uuid4()))
    assert response.status_code == 404, (
        f"issuing an invite for an unknown patient returned {response.status_code}: "
        f"{response.text[:300]}"
    )
    assert set(response.json()) == {"detail"}
