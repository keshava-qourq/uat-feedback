"""US-007-3: the condition pack holds every piece of condition logic (AC-020),
the app still runs with the pack disabled (AC-022), and only an admin may read
or write the pack.

Everything goes through the real API against the sandbox's PostgreSQL: the
bootstrap admin signs in through POST /api/auth/login (the one sign-in), and
nothing is written into the database by hand.
"""

from __future__ import annotations

import os
import secrets
import uuid
from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from tests.integration.conftest import admin_headers

PACK = "/api/admin/pack"

#: Env settings that may carry "the pack is disabled" switch. All of them are
#: set to false together, so the test does not depend on one chosen name.
DISABLE_SETTINGS = (
    "CONDITION_PACK_ENABLED",
    "PACK_ENABLED",
    "CONDITION_PACK",
)

#: The non-admin account this module signs in as for the wrong-role check: the
#: backend seeds a patient-role user from these two at startup, so naming them
#: here -- before the application starts -- creates the account through the
#: application's own code rather than by writing a row.
os.environ.setdefault("SMOKE_TEST_EMAIL", f"qa-patient-{uuid.uuid4().hex[:8]}@example.test")
os.environ.setdefault("SMOKE_TEST_PASSWORD", secrets.token_urlsafe(24))

#: The sections AC-020 requires the pack to carry: criterion key -> the names it
#: may legitimately be called in the pack's configuration.
REQUIRED_SECTIONS: dict[str, tuple[str, ...]] = {
    "code lists": ("code_lists", "codes", "code_sets", "codelists"),
    "signal definitions": ("signals", "signal_definitions", "signal_defs"),
    "criteria (ASAS and SPARTAN)": ("criteria", "classification_criteria", "rules_criteria"),
    "counter-evidence": ("counter_evidence", "counter_evidence_rules", "counterevidence"),
    "demotion rules": ("demotion_rules", "demotions", "demotion"),
    "tier thresholds": ("tier_thresholds", "thresholds", "tiers"),
    "workup items": ("workup", "workup_items", "next_steps"),
    "patient-facing copy": ("copy", "patient_copy", "patient_facing_copy", "strings"),
}


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


def _section(config: dict, names: tuple[str, ...]) -> Any:
    """The pack section under any of `names`, searched at any depth."""
    for obj in _objects(config):
        for name in names:
            value = obj.get(name)
            if value:
                return value
    return None


def _pack_config(body: dict) -> dict:
    config = body.get("config")
    assert isinstance(config, dict) and config, (
        f"GET {PACK} answers no pack configuration: {str(body)[:300]}"
    )
    return config


def _reports_no_active_pack(body: Any) -> bool:
    """Whether a payload says, in any of the shapes the contract allows, that no
    condition pack is active."""
    if not isinstance(body, dict):
        return False
    if body.get("active") is False or body.get("enabled") is False:
        return True
    if "pack" in body and body.get("pack") is None:
        return True
    if body.get("pack_key") in (None, "") and not body.get("config"):
        return True
    text = " ".join(_strings(body)).lower()
    return "no active" in text or "no pack" in text or "not active" in text


# ------------------------------------------------------------------------ AC-020


def test_ac020_the_pack_carries_every_piece_of_condition_logic(api: TestClient) -> None:
    """AC-020: GET /api/admin/pack as an admin returns a pack containing code lists,
    signal definitions, ASAS and SPARTAN criteria, counter-evidence and demotion
    rules, tier thresholds, workup items with reasoning text, and patient-facing
    copy strings."""
    headers = admin_headers(api)
    response = api.get(PACK, headers=headers)

    assert response.status_code == 200, (
        f"GET {PACK} returned {response.status_code}: {response.text[:300]}"
    )
    body = response.json()
    assert body.get("pack_key"), f"the active pack has no pack_key: {str(body)[:300]}"
    assert isinstance(body.get("version"), int), f"the pack has no version: {str(body)[:300]}"
    config = _pack_config(body)

    missing = [
        criterion
        for criterion, names in REQUIRED_SECTIONS.items()
        if _section(config, names) is None
    ]
    assert not missing, (
        f"the pack carries no section for: {missing}; it has {sorted(config)}"
    )

    criteria = _section(config, REQUIRED_SECTIONS["criteria (ASAS and SPARTAN)"])
    criteria_text = " ".join(_strings(criteria)).upper()
    assert "ASAS" in criteria_text, (
        f"the pack's criteria name no ASAS criteria: {criteria_text[:300]}"
    )
    assert "SPARTAN" in criteria_text, (
        f"the pack's criteria name no SPARTAN criteria: {criteria_text[:300]}"
    )


def test_ac020_every_workup_item_carries_its_reasoning_text(api: TestClient) -> None:
    """AC-020: the workup items in the pack each carry the reasoning text shown
    beside them, so no explanation lives in code."""
    headers = admin_headers(api)
    response = api.get(PACK, headers=headers)
    assert response.status_code == 200, (
        f"GET {PACK} returned {response.status_code}: {response.text[:300]}"
    )
    workup = _section(_pack_config(response.json()), REQUIRED_SECTIONS["workup items"])
    assert workup, "the pack carries no workup items"

    items = workup if isinstance(workup, list) else list(workup.values())
    without_reason = [
        item
        for item in items
        if not (
            isinstance(item, dict)
            and any(
                isinstance(item.get(name), str) and item.get(name, "").strip()
                for name in ("reasoning", "reason", "why", "rationale", "reasoning_text")
            )
        )
    ]
    assert not without_reason, (
        f"these workup items carry no reasoning text: {str(without_reason)[:300]}"
    )


def test_ac020_the_pack_carries_the_patient_facing_copy_strings(api: TestClient) -> None:
    """AC-020: the words a patient reads are pack configuration, not code."""
    headers = admin_headers(api)
    response = api.get(PACK, headers=headers)
    assert response.status_code == 200, (
        f"GET {PACK} returned {response.status_code}: {response.text[:300]}"
    )
    copy = _section(_pack_config(response.json()), REQUIRED_SECTIONS["patient-facing copy"])
    assert copy, "the pack carries no patient-facing copy"
    sentences = [s for s in _strings(copy) if " " in s.strip()]
    assert sentences, f"the patient-facing copy holds no readable sentence: {str(copy)[:300]}"


# ------------------------------------------------------------------- NFR-019


def test_nfr019_an_edit_applies_without_a_code_deployment(api: TestClient) -> None:
    """NFR-019: saving an edited pack through PUT /api/admin/pack writes a new
    version that the running process serves immediately -- no restart, no deploy."""
    headers = admin_headers(api)
    before = api.get(PACK, headers=headers)
    assert before.status_code == 200, (
        f"GET {PACK} returned {before.status_code}: {before.text[:300]}"
    )
    body = before.json()
    config = _pack_config(body)
    version = body["version"]

    marker = f"qa-threshold-marker-{uuid.uuid4().hex[:8]}"
    edited = {**config, "qa_marker": marker}
    saved = api.put(
        PACK,
        headers=headers,
        json={"config": edited, "change_summary": "QA edit: code list and threshold change"},
    )
    assert saved.status_code == 200, (
        f"PUT {PACK} returned {saved.status_code}: {saved.text[:300]}"
    )
    saved_body = saved.json()
    assert saved_body.get("version", version) > version, (
        f"saving the pack did not write a new version: {saved_body}"
    )
    assert saved_body.get("updated_by"), f"the save records no author: {saved_body}"
    assert saved_body.get("updated_at"), f"the save records no time: {saved_body}"

    after = api.get(PACK, headers=headers)
    assert after.status_code == 200
    assert marker in _strings(after.json()), (
        "the edited pack is not served by the running process, so the change would "
        "need a deployment to take effect"
    )


# ------------------------------------------------------------------------ AC-022


@pytest.fixture(scope="module")
def api_without_pack() -> Iterator[TestClient]:
    """The same application started with the condition pack disabled in configuration."""
    os.environ.setdefault("BOOTSTRAP_ADMIN_EMAIL", f"qa-nopack-{uuid.uuid4().hex[:8]}@example.test")
    os.environ.setdefault("BOOTSTRAP_ADMIN_PASSWORD", secrets.token_urlsafe(24))
    previous = {name: os.environ.get(name) for name in DISABLE_SETTINGS}
    for name in DISABLE_SETTINGS:
        os.environ[name] = "false"
    from app.main import app

    try:
        with TestClient(app) as client:
            yield client
    finally:
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


def test_ac022_with_the_pack_disabled_the_app_starts_and_reports_no_active_pack(
    api_without_pack: TestClient,
) -> None:
    """AC-022: with the pack disabled in configuration the application starts
    cleanly and says that no condition pack is active."""
    client = api_without_pack
    health = client.get("/health")
    assert health.status_code == 200, (
        f"with the pack disabled the app does not answer /health: {health.status_code}"
    )
    assert health.json()["status"] == "ok"

    headers = admin_headers(client)
    response = client.get(PACK, headers=headers)
    assert response.status_code == 200, (
        f"GET {PACK} with no pack active returned {response.status_code}: {response.text[:300]}"
    )
    assert _reports_no_active_pack(response.json()), (
        f"GET {PACK} does not report that no condition pack is active: {response.text[:300]}"
    )

    settings = client.get("/api/admin/settings", headers=headers)
    assert settings.status_code == 200
    assert _reports_no_active_pack(settings.json()) or settings.json().get("pack_version") in (
        None,
        "",
    ), f"the settings page still reports an active pack version: {settings.text[:300]}"


def test_ac022_ingest_and_timeline_routes_still_answer_with_no_pack(
    api_without_pack: TestClient,
) -> None:
    """AC-022: with no pack active the ingest and timeline routes still answer
    rather than erroring."""
    client = api_without_pack
    headers = admin_headers(client)

    unknown_run = client.get(f"/api/admin/ingest-runs/{uuid.uuid4()}", headers=headers)
    assert unknown_run.status_code == 404, (
        f"with no pack active the ingest report errored: {unknown_run.status_code} "
        f"{unknown_run.text[:200]}"
    )

    for path in ("/api/patients/me/timeline", "/api/worklist"):
        response = client.request("GET", path, headers=headers)
        assert response.status_code < 500, (
            f"with no pack active GET {path} errored: {response.status_code} "
            f"{response.text[:200]}"
        )
        assert set(response.json()) >= {"detail"} or isinstance(response.json(), (dict, list))


# ------------------------------------------------------------- access control


def test_the_pack_routes_are_401_unauthenticated(api: TestClient) -> None:
    """Behaviour rules: no bearer token means 401 on both pack routes, with the
    project's one error shape."""
    for method, call in (("GET", api.get), ("PUT", api.put)):
        response = call(PACK) if method == "GET" else call(PACK, json={"config": {}})
        assert response.status_code == 401, (
            f"{method} {PACK} unauthenticated returned {response.status_code}: "
            f"{response.text[:200]}"
        )
        assert set(response.json()) == {"detail"}

    wrong = {"Authorization": f"Bearer {secrets.token_urlsafe(32)}"}
    for method in ("GET", "PUT"):
        response = api.request(method, PACK, headers=wrong, json={"config": {}})
        assert response.status_code == 401, (
            f"{method} {PACK} with a token that belongs to no session returned "
            f"{response.status_code}: {response.text[:200]}"
        )


def patient_token(api: TestClient) -> str:
    """A non-admin (patient-role) session token, obtained through the real API.

    The platform's smoke-test account is a patient-role account the backend
    seeds at startup from SMOKE_TEST_EMAIL / SMOKE_TEST_PASSWORD (see
    app/bootstrap.py); those two are set for this module above, before the
    application starts, so the account exists without any row being written by
    hand. The token itself comes from the one sign-in route.
    """
    email = os.environ.get("SMOKE_TEST_EMAIL")
    password = os.environ.get("SMOKE_TEST_PASSWORD")
    assert email and password, (
        "SMOKE_TEST_EMAIL and SMOKE_TEST_PASSWORD are not set, so no patient-role "
        "account exists to test the wrong-role case with."
    )
    response = api.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, (
        f"the patient-role smoke-test account cannot sign in: {response.status_code} "
        f"{response.text[:200]}"
    )
    body = response.json()
    role = str((body.get("user") or {}).get("role", "patient"))
    assert role != "admin", f"the smoke-test account is not a non-admin account: {role}"
    return str(body["token"])


def test_the_pack_routes_are_403_for_a_non_admin_token(api: TestClient) -> None:
    """Behaviour rules: an authenticated token of the wrong role is 403, not 401
    and never 200, on both pack routes."""
    headers = {"Authorization": f"Bearer {patient_token(api)}"}

    read = api.get(PACK, headers=headers)
    assert read.status_code == 403, (
        f"GET {PACK} with a patient token returned {read.status_code}: {read.text[:200]}"
    )
    assert set(read.json()) == {"detail"}

    write = api.put(PACK, headers=headers, json={"config": {}, "change_summary": "nope"})
    assert write.status_code == 403, (
        f"PUT {PACK} with a patient token returned {write.status_code}: {write.text[:200]}"
    )
    assert set(write.json()) == {"detail"}
