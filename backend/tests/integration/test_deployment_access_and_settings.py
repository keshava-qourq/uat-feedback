"""US-044-3: the deployed application refuses unauthenticated access, reports its
health and active dataset version, and never shows a credential value.

Everything here goes through the real API against the sandbox's real PostgreSQL
and Redis: the bootstrap admin signs in through POST /api/auth/login, and the
dataset version AC-144 checks comes from an ingest run started through
POST /api/admin/ingest-runs -- no row is written by hand and no source or env
file is read for a credential value. The one value a test compares against is
the one this process already holds in `os.environ`, so a leak is detected
without ever writing a credential down.
"""

from __future__ import annotations

import json
import os
import secrets
import uuid

from fastapi.testclient import TestClient

from tests.integration import fixtures_dataset as fx
from tests.integration.conftest import admin_headers, start_ingest, wait_for_run

SETTINGS = "/api/admin/settings"

#: Routes a patient or clinician uses. None of them may answer without a session.
PROTECTED_ROUTES: list[tuple[str, str]] = [
    ("GET", "/api/worklist"),
    ("GET", "/api/patients/me/timeline"),
    ("GET", "/api/patients/me/updates"),
    ("GET", "/api/patients/me/visit-prep"),
    ("GET", "/api/patients/me/visit-prep.pdf"),
    ("GET", "/api/demo/personas"),
    ("GET", "/api/evaluation/runs/latest"),
    ("GET", "/api/auth/me"),
    ("GET", SETTINGS),
]

#: Any of these names may carry the hosted language-model credential.
LLM_KEY_NAMES = ("ANTHROPIC_API_KEY", "LLM_API_KEY")


def _wrong_bearer() -> dict[str, str]:
    """A syntactically valid bearer token that belongs to no session."""
    return {"Authorization": f"Bearer {secrets.token_urlsafe(32)}"}


def _drain_ingest_queue() -> None:
    """Run whatever is on the ingest queue, as the deployed RQ worker would."""
    import redis
    from rq import Queue, SimpleWorker

    connection = redis.from_url(os.environ["REDIS_URL"])
    queue = Queue("ingest", connection=connection)
    SimpleWorker([queue], connection=connection).work(burst=True)


def _unique_heroes_json() -> bytes:
    suffix = uuid.uuid4().hex[:8]
    return json.dumps(
        [
            {
                "persona_key": f"settings-ada-{suffix}",
                "name": "Ada Lovelace",
                "one_line_description": "Classic presentation missed for years.",
                "patient_id": "P0001",
                "cutoff_date": "2021-01-01",
            }
        ]
    ).encode()


def _ingest_a_dataset_version(api: TestClient, headers: dict[str, str]) -> str:
    """Load the fixture set through the real ingest API; return its dataset version."""
    files = fx.fixture_set(**{"heroes.json": _unique_heroes_json()})
    source_uri, _prefix = fx.upload_fixture_set(files)
    version = f"qa-settings-{uuid.uuid4().hex[:8]}"
    _drain_ingest_queue()
    started = start_ingest(api, headers, dataset_version=version, source_uri=source_uri, seed=5)
    _drain_ingest_queue()
    report = wait_for_run(api, headers, started["run_id"])
    assert str(report["run"]["status"]).lower() in {"succeeded", "success", "completed"}, (
        f"the ingest run did not pass, so there is no latest passed run: {report['run']}"
    )
    return version


def _all_strings(payload: object) -> list[str]:
    if isinstance(payload, str):
        return [payload]
    if isinstance(payload, dict):
        out: list[str] = []
        for key, value in payload.items():
            out.append(str(key))
            out.extend(_all_strings(value))
        return out
    if isinstance(payload, list):
        out = []
        for item in payload:
            out.extend(_all_strings(item))
        return out
    return [] if payload is None else [str(payload)]


# --------------------------------------------------------------- AC-146 / NFR-010


def test_ac146_nfr010_an_unauthenticated_request_is_refused(api: TestClient) -> None:
    """AC-146 / NFR-010: no Authorization header means 401 on the ingest report and
    on the settings page, with the project's one error shape."""
    for path in (f"/api/admin/ingest-runs/{uuid.uuid4()}", SETTINGS):
        response = api.get(path)
        assert response.status_code == 401, (
            f"GET {path} without a token returned {response.status_code}: {response.text[:200]}"
        )
        assert set(response.json()) == {"detail"}, (
            f"GET {path} answered an error body other than {{detail}}: {response.text[:200]}"
        )


def test_ac146_nfr010_a_wrong_bearer_is_refused(api: TestClient) -> None:
    """AC-146: a bearer token that belongs to no session is 401, not 403 and not 200."""
    headers = _wrong_bearer()
    for path in (f"/api/admin/ingest-runs/{uuid.uuid4()}", SETTINGS):
        response = api.get(path, headers=headers)
        assert response.status_code == 401, (
            f"GET {path} with a wrong bearer returned {response.status_code}: "
            f"{response.text[:200]}"
        )
        assert set(response.json()) == {"detail"}


def test_ac146_health_succeeds_unauthenticated(api: TestClient) -> None:
    """AC-146: the liveness probe is the one route that answers with no token."""
    response = api.get("/health")

    assert response.status_code == 200, (
        f"GET /health unauthenticated returned {response.status_code}: {response.text[:200]}"
    )
    assert response.json()["status"] == "ok"


def test_nfr010_every_patient_and_clinician_route_refuses_an_anonymous_request(
    api: TestClient,
) -> None:
    """NFR-010: no patient or clinician route serves data without a session."""
    served = []
    for method, path in PROTECTED_ROUTES:
        anonymous = api.request(method, path)
        wrong = api.request(method, path, headers=_wrong_bearer())
        if anonymous.status_code != 401 or wrong.status_code != 401:
            served.append((f"{method} {path}", anonymous.status_code, wrong.status_code))
    assert not served, (
        "these routes answered something other than 401 to an anonymous and/or a "
        f"wrong-token request (path, anonymous, wrong-token): {served}"
    )


def test_nfr010_the_api_offers_no_public_sign_up_or_self_service_entry_point(
    api: TestClient,
) -> None:
    """NFR-010: access is only ever by invitation -- there is no registration route,
    and any route that does exist for an invited user needs its token."""
    document = api.get("/openapi.json")
    assert document.status_code == 200
    paths = document.json()["paths"]

    forbidden = [
        path
        for path in paths
        if any(word in path.lower() for word in ("signup", "sign-up", "register", "registration"))
    ]
    assert not forbidden, f"the API exposes a self-service sign-up entry point: {forbidden}"

    for path in ("/api/auth/register", "/api/auth/signup", "/api/users"):
        response = api.post(path, json={"email": "nobody@example.test"})
        assert response.status_code in (401, 404, 405), (
            f"POST {path} answered {response.status_code}: a self-service account "
            "creation route must not exist"
        )


# ------------------------------------------------------------------------ AC-144


def test_ac144_health_reports_ok_and_the_services_it_depends_on(api: TestClient) -> None:
    """AC-144: the deployed application and its PostgreSQL event store are up, so the
    health check passes against the real database."""
    response = api.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["db"] is True, (
        "the health check reports the PostgreSQL unified-event store as unreachable"
    )


def test_ac144_settings_reports_the_latest_passed_runs_dataset_version(
    api: TestClient,
) -> None:
    """AC-144: the administrator page reports the active dataset version -- the one
    of the latest passed ingest run, created here through the real ingest API."""
    headers = admin_headers(api)
    version = _ingest_a_dataset_version(api, headers)

    response = api.get(SETTINGS, headers=headers)
    assert response.status_code == 200, (
        f"GET {SETTINGS} returned {response.status_code}: {response.text[:200]}"
    )
    body = response.json()
    assert body.get("dataset_version") == version, (
        f"the settings page reports dataset_version {body.get('dataset_version')!r}; the "
        f"latest passed ingest run loaded {version!r}"
    )
    assert body.get("health"), f"the settings page reports no health result: {body}"


# ------------------------------------------------------------- AC-145 / NFR-011


def test_ac145_nfr011_settings_never_contains_a_credential_value(api: TestClient) -> None:
    """AC-145 / NFR-011: the settings payload shows a masked placeholder -- never the
    raw DATABASE_URL and never the language-model key."""
    headers = admin_headers(api)
    response = api.get(SETTINGS, headers=headers)
    assert response.status_code == 200, (
        f"GET {SETTINGS} returned {response.status_code}: {response.text[:200]}"
    )
    text = response.text
    strings = _all_strings(response.json())

    database_url = os.environ.get("DATABASE_URL")
    assert database_url, "DATABASE_URL is not set in this environment"
    assert database_url not in text, "the settings page leaks the raw DATABASE_URL"
    password = database_url.rsplit("@", 1)[0].rsplit(":", 1)[-1]
    if password and len(password) > 3:
        assert password not in text, "the settings page leaks the database password"

    for name in LLM_KEY_NAMES:
        value = os.environ.get(name)
        if value:
            assert value not in text, f"the settings page leaks the value of {name}"

    assert any("not-shown" in s or "*" in s or "masked" in s.lower() for s in strings), (
        f"no credential is shown as a masked placeholder: {text[:300]}"
    )


def test_ac145_nfr011_settings_reports_connected_for_configured_credentials(
    api: TestClient,
) -> None:
    """AC-145: with the database connection and the language-model key set in this
    environment, both are reported 'connected' rather than 'not configured'."""
    if not any(os.environ.get(name) for name in LLM_KEY_NAMES):
        # Supplied as deployment configuration (NFR-011): set it here for this
        # process only, with a value generated at run time and written nowhere.
        os.environ["ANTHROPIC_API_KEY"] = secrets.token_urlsafe(32)

    headers = admin_headers(api)
    response = api.get(SETTINGS, headers=headers)
    assert response.status_code == 200, (
        f"GET {SETTINGS} returned {response.status_code}: {response.text[:200]}"
    )
    body = response.json()
    credentials = body.get("credentials")
    assert isinstance(credentials, list) and credentials, (
        f"the settings page lists no credentials: {str(body)[:300]}"
    )

    by_status = {
        str(item.get("name", "")).lower(): str(item.get("status", "")).lower()
        for item in credentials
    }
    assert any("database" in name or name == "database_url" for name in by_status), (
        f"the database connection is not listed among the credentials: {by_status}"
    )
    assert any("llm" in name or "model" in name or "anthropic" in name for name in by_status), (
        f"the language-model credential is not listed among the credentials: {by_status}"
    )
    not_connected = {name: status for name, status in by_status.items() if status != "connected"}
    assert not not_connected, (
        f"these credentials are set in this environment but are not reported connected: "
        f"{not_connected}"
    )


def test_nfr011_no_credential_value_appears_in_any_api_response_or_the_openapi_document(
    api: TestClient,
) -> None:
    """NFR-011: no screen's payload, and not the published API document, carries a
    credential value."""
    headers = admin_headers(api)
    secrets_in_use = [
        value
        for value in (os.environ.get("DATABASE_URL"), *(os.environ.get(n) for n in LLM_KEY_NAMES))
        if value
    ]

    leaking: list[str] = []
    for method, path in [*PROTECTED_ROUTES, ("GET", "/openapi.json"), ("GET", "/health")]:
        response = api.request(method, path, headers=headers)
        if response.status_code != 200:
            continue
        body = response.text
        if any(value in body for value in secrets_in_use):
            leaking.append(f"{method} {path}")
    assert not leaking, f"these responses carry a credential value: {leaking}"
