"""US-031-3: sign-in, sign-out, idle expiry, deactivation and password storage,
proved against the real API (AC-100..AC-104, NFR-007, NFR-008).

Everything goes through the real HTTP API against the sandbox's PostgreSQL:
the bootstrap admin signs in through POST /api/auth/login, and every clinician
account, password and session this file needs is created by calling the admin
and auth routes -- no row is written by hand. Each test creates its own
account and issues its own sessions, so concurrent tests never share a token.

No password is written down anywhere: each one is generated at run time.

Idle expiry (AC-102) needs a short idle window, which is deployment
configuration. The candidate setting names are set here at import time --
before the application is imported by the `api` fixture -- so the running
process picks up a short window rather than the thirty-minute default.
"""

from __future__ import annotations

import os
import secrets
import time
import uuid
from typing import Any

import pytest
from fastapi.testclient import TestClient

from tests.integration.conftest import admin_headers

ADMIN_USERS = "/api/admin/users"
LOGIN = "/api/auth/login"
LOGOUT = "/api/auth/logout"
ME = "/api/auth/me"
SET_PASSWORD = "/api/auth/set-password"
CLINICIAN_ROUTE = "/api/worklist"

#: The idle window this run configures, in seconds, and the names it may be
#: read from. Minute-granularity names get the nearest whole minute.
IDLE_SECONDS = 30
IDLE_SETTINGS_SECONDS = (
    "SESSION_IDLE_SECONDS",
    "SESSION_IDLE_TIMEOUT_SECONDS",
    "IDLE_TIMEOUT_SECONDS",
    "SESSION_IDLE_TIMEOUT",
)
IDLE_SETTINGS_MINUTES = (
    "SESSION_IDLE_MINUTES",
    "SESSION_IDLE_TIMEOUT_MINUTES",
    "IDLE_TIMEOUT_MINUTES",
)

for _name in IDLE_SETTINGS_SECONDS:
    os.environ.setdefault(_name, str(IDLE_SECONDS))
for _name in IDLE_SETTINGS_MINUTES:
    os.environ.setdefault(_name, "1")

#: The idle window the idle-expiry test configures for its own run, in seconds,
#: and how long it then leaves its idle session untouched (the window plus slack).
SHORT_IDLE_SECONDS = 30
IDLE_WAIT_SECONDS = 45

#: The key a one-time password-set token may arrive under in the create
#: response. It is shown once, there and nowhere else.
TOKEN_KEYS = (
    "set_password_token",
    "password_set_token",
    "password_token",
    "invite_token",
    "token",
)


def _new_password() -> str:
    return secrets.token_urlsafe(24)


def _strings(payload: Any) -> list[str]:
    if isinstance(payload, str):
        return [payload]
    if isinstance(payload, dict):
        out: list[str] = []
        for key, value in payload.items():
            out.append(str(key))
            out.extend(_strings(value))
        return out
    if isinstance(payload, list):
        out = []
        for item in payload:
            out.extend(_strings(item))
        return out
    return [] if payload is None else [str(payload)]


def _objects(payload: Any) -> list[dict]:
    found: list[dict] = []
    if isinstance(payload, dict):
        found.append(payload)
        for value in payload.values():
            found.extend(_objects(value))
    elif isinstance(payload, list):
        for item in payload:
            found.extend(_objects(item))
    return found


def _find(payload: Any, keys: tuple[str, ...]) -> str | None:
    for obj in _objects(payload):
        for key in keys:
            value = obj.get(key)
            if isinstance(value, str) and value.strip():
                return value
    return None


def create_clinician(api: TestClient, headers: dict[str, str]) -> tuple[str, str, str | None]:
    """Create a clinician through the admin API.

    Returns `(user_id, email, one-time password-set token or None)`. Called
    from the test body so a missing route fails the criterion rather than a
    fixture.
    """
    email = f"qa-clinician-{uuid.uuid4().hex[:10]}@example.test"
    response = api.post(ADMIN_USERS, headers=headers, json={"email": email, "role": "clinician"})
    assert response.status_code in (200, 201), (
        f"POST {ADMIN_USERS} returned {response.status_code}: {response.text[:300]}"
    )
    body = response.json()
    user_id = _find(body, ("id", "user_id"))
    assert user_id, f"the created account carries no id: {str(body)[:300]}"
    return user_id, email, _find(body, TOKEN_KEYS)


def set_password(api: TestClient, token: str, password: str) -> Any:
    return api.post(SET_PASSWORD, json={"token": token, "password": password})


def login(api: TestClient, email: str, password: str) -> Any:
    return api.post(LOGIN, json={"email": email, "password": password})


def sign_in_clinician(api: TestClient, headers: dict[str, str]) -> tuple[str, str, str]:
    """A brand new clinician who has set a password and signed in.

    Returns `(user_id, email, password)`.
    """
    user_id, email, token = create_clinician(api, headers)
    password = _new_password()
    assert token, (
        "creating an account answered no one-time password-set token, so the new "
        "account can never be used (NFR-008: accounts start with no usable password)"
    )
    done = set_password(api, token, password)
    assert done.status_code in (200, 204), (
        f"POST {SET_PASSWORD} returned {done.status_code}: {done.text[:300]}"
    )
    return user_id, email, password


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# ------------------------------------------------------------------------ AC-100


def test_ac100_a_clinician_can_sign_in_and_reach_the_worklist(api: TestClient) -> None:
    """AC-100: a clinician created through the API signs in, reaches
    GET /api/worklist with the returned bearer, and GET /api/auth/me attributes
    the session to that account."""
    admin = admin_headers(api)
    _user_id, email, password = sign_in_clinician(api, admin)

    signed_in = login(api, email, password)
    assert signed_in.status_code == 200, (
        f"the clinician cannot sign in: {signed_in.status_code} {signed_in.text[:300]}"
    )
    token = signed_in.json().get("token")
    assert isinstance(token, str) and token, (
        f"login answered no bearer token in its body: {signed_in.text[:300]}"
    )

    worklist = api.get(CLINICIAN_ROUTE, headers=bearer(token))
    assert worklist.status_code == 200, (
        f"GET {CLINICIAN_ROUTE} with the clinician's bearer returned "
        f"{worklist.status_code}: {worklist.text[:300]}"
    )

    me = api.get(ME, headers=bearer(token))
    assert me.status_code == 200, f"GET {ME} returned {me.status_code}: {me.text[:300]}"
    body = me.json()
    assert str(body.get("email", "")).lower() == email.lower(), (
        f"GET {ME} attributes the session to {body.get('email')!r}, not to {email!r}"
    )
    assert body.get("role") == "clinician", (
        f"GET {ME} reports role {body.get('role')!r} for a clinician account"
    )


def test_ac100_login_compares_the_email_case_insensitively(api: TestClient) -> None:
    """AC-100 / behaviour rules: the email is the one case-insensitive identifier."""
    admin = admin_headers(api)
    _user_id, email, password = sign_in_clinician(api, admin)

    response = login(api, email.upper(), password)
    assert response.status_code == 200, (
        f"signing in with the address in upper case returned {response.status_code}: "
        f"{response.text[:300]}"
    )


# -------------------------------------------------------------- AC-101 / NFR-007


def test_ac101_nfr007_logout_ends_only_the_session_it_was_called_with(api: TestClient) -> None:
    """AC-101 / NFR-007: after POST /api/auth/logout that token is 401 on a
    clinician route, while a second session issued for the same user before the
    logout still works."""
    admin = admin_headers(api)
    _user_id, email, password = sign_in_clinician(api, admin)

    first = login(api, email, password)
    second = login(api, email, password)
    assert first.status_code == 200 and second.status_code == 200, (
        f"the clinician could not open two sessions: {first.status_code} / "
        f"{second.status_code}"
    )
    first_token = first.json()["token"]
    second_token = second.json()["token"]
    assert first_token != second_token, (
        "signing in twice returned the same token, so the second sign-in did not open "
        "its own session"
    )

    signed_out = api.post(LOGOUT, headers=bearer(first_token))
    assert signed_out.status_code in (200, 204), (
        f"POST {LOGOUT} returned {signed_out.status_code}: {signed_out.text[:300]}"
    )

    revoked = api.get(CLINICIAN_ROUTE, headers=bearer(first_token))
    assert revoked.status_code == 401, (
        f"after signing out, GET {CLINICIAN_ROUTE} with that token returned "
        f"{revoked.status_code}: {revoked.text[:200]}"
    )
    assert set(revoked.json()) == {"detail"}

    still_live = api.get(CLINICIAN_ROUTE, headers=bearer(second_token))
    assert still_live.status_code == 200, (
        "signing out of one session ended the user's other session: "
        f"GET {CLINICIAN_ROUTE} returned {still_live.status_code}"
    )
    me = api.get(ME, headers=bearer(second_token))
    assert me.status_code == 200, f"the other session no longer answers {ME}: {me.status_code}"


# -------------------------------------------------------------- AC-102 / NFR-007


def test_ac102_nfr007_an_idle_session_expires_while_an_active_one_stays_valid(
    api: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-102 / NFR-007: a session whose configured idle window has elapsed is 401
    on its next call, while a session that keeps calling stays valid throughout.

    The idle token is not touched at all while it idles: every authenticated call
    refreshes the window (behaviour rules), so the only honest check is to let the
    window elapse untouched and then make one single call.
    """
    for name in IDLE_SETTINGS_SECONDS:
        monkeypatch.setenv(name, str(SHORT_IDLE_SECONDS))
    for name in IDLE_SETTINGS_MINUTES:
        monkeypatch.setenv(name, str(SHORT_IDLE_SECONDS / 60))

    admin = admin_headers(api)
    _user_id, email, password = sign_in_clinician(api, admin)

    idle = login(api, email, password)
    active = login(api, email, password)
    assert idle.status_code == 200 and active.status_code == 200
    idle_token = idle.json()["token"]
    active_token = active.json()["token"]

    # Both sessions answer to begin with.
    assert api.get(CLINICIAN_ROUTE, headers=bearer(idle_token)).status_code == 200
    assert api.get(ME, headers=bearer(active_token)).status_code == 200

    # The idle token is left strictly untouched while the window elapses; only the
    # active session keeps calling, which must keep it alive.
    started = time.monotonic()
    while time.monotonic() - started < IDLE_WAIT_SECONDS:
        time.sleep(5)
        keep_alive = api.get(ME, headers=bearer(active_token))
        assert keep_alive.status_code == 200, (
            "a session that keeps calling was refused after "
            f"{time.monotonic() - started:.0f}s: {keep_alive.status_code} "
            f"{keep_alive.text[:200]}"
        )

    lapsed = api.get(CLINICIAN_ROUTE, headers=bearer(idle_token))
    assert lapsed.status_code == 401, (
        f"a session left untouched for {IDLE_WAIT_SECONDS}s with the idle window "
        f"configured to {SHORT_IDLE_SECONDS}s "
        f"({IDLE_SETTINGS_SECONDS + IDLE_SETTINGS_MINUTES}) answered "
        f"{lapsed.status_code}; an idle session must expire so the next action asks "
        "the user to sign in again"
    )
    assert set(lapsed.json()) == {"detail"}

    still_live = api.get(CLINICIAN_ROUTE, headers=bearer(active_token))
    assert still_live.status_code == 200, (
        "the session that kept calling expired as well, so activity does not keep a "
        f"session alive: {still_live.status_code}"
    )


# -------------------------------------------------------------- AC-103 / NFR-007


def test_ac103_nfr007_deactivation_revokes_every_session_and_blocks_later_sign_in(
    api: TestClient,
) -> None:
    """AC-103 / NFR-007: after POST /api/admin/users/{id}/deactivate every existing
    token for that user is 401, and a later login with the correct password is 401
    with exactly the same detail as a wrong password."""
    admin = admin_headers(api)
    user_id, email, password = sign_in_clinician(api, admin)

    tokens = []
    for _ in range(2):
        response = login(api, email, password)
        assert response.status_code == 200
        tokens.append(response.json()["token"])
    for token in tokens:
        assert api.get(CLINICIAN_ROUTE, headers=bearer(token)).status_code == 200

    wrong = login(api, email, _new_password())
    assert wrong.status_code == 401, (
        f"a wrong password returned {wrong.status_code}: {wrong.text[:200]}"
    )
    wrong_detail = wrong.json()["detail"]

    deactivated = api.post(f"{ADMIN_USERS}/{user_id}/deactivate", headers=admin)
    assert deactivated.status_code in (200, 204), (
        f"POST {ADMIN_USERS}/{{id}}/deactivate returned {deactivated.status_code}: "
        f"{deactivated.text[:300]}"
    )

    still_working = []
    for index, token in enumerate(tokens):
        response = api.get(CLINICIAN_ROUTE, headers=bearer(token))
        if response.status_code != 401:
            still_working.append((index, response.status_code))
        else:
            assert set(response.json()) == {"detail"}
    assert not still_working, (
        f"these sessions of the deactivated account still answer (index, status): "
        f"{still_working}"
    )

    after = login(api, email, password)
    assert after.status_code == 401, (
        f"the deactivated account signed in again with the correct password: "
        f"{after.status_code} {after.text[:200]}"
    )
    assert set(after.json()) == {"detail"}
    assert after.json()["detail"] == wrong_detail, (
        "a deactivated account and a wrong password answer different details, so the "
        f"two can be told apart: {after.json()['detail']!r} vs {wrong_detail!r}"
    )


def test_ac103_deactivating_an_unknown_user_is_404(api: TestClient) -> None:
    """AC-103 / behaviour rules: an unknown user id is not found, not a silent pass."""
    admin = admin_headers(api)
    response = api.post(f"{ADMIN_USERS}/{uuid.uuid4()}/deactivate", headers=admin)

    assert response.status_code == 404, (
        f"deactivating an unknown user returned {response.status_code}: {response.text[:200]}"
    )
    assert set(response.json()) == {"detail"}


# -------------------------------------------------------------- AC-104 / NFR-008


def test_ac104_nfr008_an_account_without_a_password_cannot_log_in_until_it_is_set(
    api: TestClient,
) -> None:
    """AC-104 / NFR-008: a new account has no usable password; it cannot log in
    until POST /api/auth/set-password is used with its one-time token."""
    admin = admin_headers(api)
    _user_id, email, token = create_clinician(api, admin)
    assert token, (
        "creating an account answered no one-time password-set token, so the user can "
        "never set their own password at first sign-in"
    )

    before = login(api, email, _new_password())
    assert before.status_code == 401, (
        f"an account with no password set answered {before.status_code} to a login "
        f"attempt: {before.text[:200]}"
    )

    password = _new_password()
    done = set_password(api, token, password)
    assert done.status_code in (200, 204), (
        f"POST {SET_PASSWORD} returned {done.status_code}: {done.text[:300]}"
    )

    after = login(api, email, password)
    assert after.status_code == 200, (
        f"after setting a password the account still cannot sign in: {after.status_code} "
        f"{after.text[:200]}"
    )
    assert isinstance(after.json().get("token"), str)


def test_ac104_re_using_a_password_set_token_is_409(api: TestClient) -> None:
    """AC-104: a consumed password-set token is refused with 409."""
    admin = admin_headers(api)
    _user_id, _email, token = create_clinician(api, admin)
    assert token, "creating an account answered no one-time password-set token"

    first = set_password(api, token, _new_password())
    assert first.status_code in (200, 204), (
        f"the first use of the token returned {first.status_code}: {first.text[:300]}"
    )

    second = set_password(api, token, _new_password())
    assert second.status_code == 409, (
        f"re-using a consumed password-set token returned {second.status_code}: "
        f"{second.text[:200]}"
    )
    assert set(second.json()) == {"detail"}


def test_ac104_an_unknown_password_set_token_is_404(api: TestClient) -> None:
    """AC-104 / behaviour rules: a token that belongs to no account is not found."""
    response = set_password(api, secrets.token_urlsafe(32), _new_password())

    assert response.status_code == 404, (
        f"an unknown password-set token returned {response.status_code}: {response.text[:200]}"
    )
    assert set(response.json()) == {"detail"}


def test_ac104_nfr008_no_response_ever_returns_a_password_or_a_recoverable_token(
    api: TestClient,
) -> None:
    """AC-104 / NFR-008: passwords are held only as salted hashes -- no route hands
    back a password, a password hash, or a live token value."""
    admin = admin_headers(api)
    user_id, email, token = create_clinician(api, admin)
    assert token, "creating an account answered no one-time password-set token"
    password = _new_password()
    assert set_password(api, token, password).status_code in (200, 204)

    signed_in = login(api, email, password)
    assert signed_in.status_code == 200
    session_token = signed_in.json()["token"]

    payloads: dict[str, Any] = {}
    for path in (ADMIN_USERS, f"{ADMIN_USERS}/{user_id}"):
        response = api.get(path, headers=admin)
        if response.status_code == 200:
            payloads[path] = response.json()
    me = api.get(ME, headers=bearer(session_token))
    assert me.status_code == 200
    payloads[ME] = me.json()
    payloads[LOGIN] = signed_in.json()

    leaking: list[str] = []
    for path, payload in payloads.items():
        values = set(_strings(payload))
        if password in values:
            leaking.append(f"{path}: the password itself")
        if token in values and path != LOGIN:
            leaking.append(f"{path}: the one-time password-set token")
        if any(value.startswith("$2") for value in values):
            leaking.append(f"{path}: a password hash")
        if any(key in ("password", "password_hash") for key in values):
            leaking.append(f"{path}: a password field")
    assert not leaking, f"these responses carry a password or a recoverable token: {leaking}"

    # The session token itself is never readable back either.
    for path, payload in payloads.items():
        if path == LOGIN:
            continue
        assert session_token not in set(_strings(payload)), (
            f"{path} hands back a live session token value"
        )


# ------------------------------------------------- no cookies: the token is the session


@pytest.mark.parametrize("path", [LOGIN, LOGOUT, ME, CLINICIAN_ROUTE])
def test_ac100_no_response_carries_set_cookie_and_the_token_is_in_the_login_body(
    api: TestClient, path: str
) -> None:
    """AC-100 / behaviour rules: login's token arrives in the JSON body and the
    server never issues Set-Cookie on any session route."""
    admin = admin_headers(api)
    _user_id, email, password = sign_in_clinician(api, admin)

    signed_in = login(api, email, password)
    assert signed_in.status_code == 200
    assert "set-cookie" not in {name.lower() for name in signed_in.headers}, (
        f"POST {LOGIN} issued a cookie: {signed_in.headers.get('set-cookie')}"
    )
    assert isinstance(signed_in.json().get("token"), str), (
        f"login's token does not arrive in the JSON body: {signed_in.text[:300]}"
    )
    token = signed_in.json()["token"]

    response = (
        api.post(path, headers=bearer(token))
        if path in (LOGIN, LOGOUT)
        else api.get(path, headers=bearer(token))
    )
    assert "set-cookie" not in {name.lower() for name in response.headers}, (
        f"{path} issued a cookie: {response.headers.get('set-cookie')}"
    )
    assert not api.cookies, f"the server set cookies on the client: {dict(api.cookies)}"
