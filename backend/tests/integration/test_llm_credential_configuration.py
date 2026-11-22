"""US-017: the hosted language-model credential is deployment configuration only
(AC-056, AC-057, NFR-011).

Everything goes through the real API against the sandbox's PostgreSQL: the
bootstrap admin signs in through POST /api/auth/login and the settings page is
read through GET /api/admin/settings. No credential value is ever written into
this file -- the only value compared against is the one this process already
holds in `os.environ`, or one generated here at run time for this process only.
"""

from __future__ import annotations

import logging
import os
import secrets
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from tests.integration.conftest import admin_headers

SETTINGS = "/api/admin/settings"

#: Any of these names may carry the hosted language-model credential, supplied
#: as deployment configuration (<llm-api-key>).
LLM_KEY_NAMES = ("ANTHROPIC_API_KEY", "LLM_API_KEY")

#: The repository root, for the "never written into source control" scan.
REPO_ROOT = Path(__file__).resolve().parents[3]

#: Directories a scan of what is committed must not walk into.
SKIPPED_DIRS = {
    ".git",
    ".venv",
    "node_modules",
    "__pycache__",
    "dist",
    "build",
    "coverage",
    "test-results",
    ".pytest_cache",
    ".ruff_cache",
    "htmlcov",
}

CONNECTED = "connected"
#: The two spellings of "no credential configured" the application uses.
NOT_CONFIGURED = ("not-configured", "not configured", "not_configured")


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


def _llm_status(body: Any) -> str:
    """The language-model connection status the settings payload reports."""
    llm = body.get("llm") if isinstance(body, dict) else None
    if isinstance(llm, dict) and llm.get("status"):
        return str(llm["status"]).strip().lower()
    if isinstance(llm, str) and llm.strip():
        return llm.strip().lower()
    for item in _objects(body):
        name = str(item.get("name", "")).lower()
        if any(word in name for word in ("llm", "anthropic", "model")) and item.get("status"):
            return str(item["status"]).strip().lower()
    raise AssertionError(
        "the settings page reports no connection status for the language-model "
        f"credential: {str(body)[:300]}"
    )


def _llm_credential_entry(body: Any) -> dict:
    """The credentials-list entry for the language-model credential."""
    for item in _objects(body):
        name = str(item.get("name", "")).lower()
        if any(word in name for word in ("llm", "anthropic", "model")) and "status" in item:
            return item
    raise AssertionError(
        f"the settings page lists no language-model credential entry: {str(body)[:300]}"
    )


def _configured_llm_value() -> str:
    """The language-model credential this process holds, setting one if absent.

    NFR-011 says the credential arrives as deployment configuration, so when the
    sandbox has none a value is generated at run time and set for this process
    only -- it is written nowhere.
    """
    for name in LLM_KEY_NAMES:
        value = (os.environ.get(name) or "").strip()
        if value:
            return value
    generated = secrets.token_urlsafe(32)
    os.environ["ANTHROPIC_API_KEY"] = generated
    return generated


def _text_files() -> list[Path]:
    found: list[Path] = []
    for path in REPO_ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIPPED_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".gz", ".ico", ".woff"}:
            continue
        if path.stat().st_size > 2_000_000:
            continue
        found.append(path)
    return found


# ------------------------------------------------------------- AC-056 / NFR-011


def test_ac056_nfr011_the_llm_credential_is_read_from_deployment_configuration(
    api: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-056: the application reads the language-model credential from configuration
    alone -- setting it makes the connection status connected, removing it makes it
    not configured, with no restart and no code change."""
    _configured_llm_value()
    headers = admin_headers(api)

    configured = api.get(SETTINGS, headers=headers)
    assert configured.status_code == 200, (
        f"GET {SETTINGS} returned {configured.status_code}: {configured.text[:200]}"
    )
    assert _llm_status(configured.json()) == CONNECTED, (
        "with the language-model credential supplied as configuration the settings "
        f"page reports {_llm_status(configured.json())!r}, not 'connected'"
    )

    for name in LLM_KEY_NAMES:
        monkeypatch.delenv(name, raising=False)
    removed = api.get(SETTINGS, headers=headers)
    assert removed.status_code == 200, (
        f"GET {SETTINGS} with no credential configured returned {removed.status_code}: "
        f"{removed.text[:200]}"
    )
    assert _llm_status(removed.json()) in NOT_CONFIGURED, (
        "with no language-model credential in the environment the settings page "
        f"reports {_llm_status(removed.json())!r}, not 'not configured': the credential "
        "is not being read from deployment configuration"
    )


def test_ac056_nfr011_the_llm_credential_value_is_in_no_file_in_source_control() -> None:
    """AC-056: the credential value this deployment uses appears in no file of the
    repository -- it lives in configuration, never in the code."""
    value = _configured_llm_value()
    assert len(value) >= 8, "the configured language-model credential is implausibly short"

    offenders: list[str] = []
    for path in _text_files():
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if value in text:
            offenders.append(str(path.relative_to(REPO_ROOT)))
    assert not offenders, (
        f"the language-model credential value appears in these files: {offenders}"
    )


def test_ac056_nfr011_no_log_line_written_while_serving_the_settings_page_carries_it(
    api: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    """AC-056: reading the settings page writes no log line containing the
    language-model credential value."""
    value = _configured_llm_value()
    headers = admin_headers(api)

    with caplog.at_level(logging.DEBUG):
        response = api.get(SETTINGS, headers=headers)
    assert response.status_code == 200, (
        f"GET {SETTINGS} returned {response.status_code}: {response.text[:200]}"
    )
    assert value not in caplog.text, (
        "a log line written while serving the settings page carries the "
        "language-model credential value"
    )


def test_ac056_nfr011_no_screen_payload_carries_the_llm_credential_value(
    api: TestClient,
) -> None:
    """AC-056: no payload any screen reads -- the settings page, health, or the
    published API document -- carries the credential value."""
    value = _configured_llm_value()
    headers = admin_headers(api)

    leaking: list[str] = []
    for path in (SETTINGS, "/health", "/openapi.json"):
        response = api.get(path, headers=headers)
        if response.status_code == 200 and value in response.text:
            leaking.append(path)
    assert not leaking, f"these responses carry the language-model credential value: {leaking}"


# ------------------------------------------------------------- AC-057 / NFR-011


def test_ac057_nfr011_the_settings_page_shows_a_masked_placeholder_and_connected(
    api: TestClient,
) -> None:
    """AC-057: with the credential configured, the settings page shows it only as a
    masked placeholder and reports the connection status as connected."""
    value = _configured_llm_value()
    headers = admin_headers(api)

    response = api.get(SETTINGS, headers=headers)
    assert response.status_code == 200, (
        f"GET {SETTINGS} returned {response.status_code}: {response.text[:200]}"
    )
    body = response.json()
    assert value not in response.text, "the settings page shows the credential value itself"

    entry = _llm_credential_entry(body)
    assert str(entry.get("status", "")).strip().lower() == CONNECTED, (
        f"the language-model credential is configured but the settings page reports "
        f"{entry.get('status')!r}"
    )
    placeholder = str(entry.get("value", ""))
    assert placeholder, (
        f"the language-model credential entry shows no masked placeholder: {entry}"
    )
    assert placeholder != value, "the credential entry shows the credential value itself"
    assert "not-shown" in placeholder.lower() or "mask" in placeholder.lower() or "*" in (
        placeholder
    ), f"the credential is not shown as a masked placeholder: {placeholder!r}"


def test_ac057_nfr011_an_unconfigured_credential_reads_not_configured(
    api: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-057: with no credential configured, the settings page still answers and the
    connection status reads not configured -- never an error and never a value."""
    for name in LLM_KEY_NAMES:
        monkeypatch.delenv(name, raising=False)
    headers = admin_headers(api)

    response = api.get(SETTINGS, headers=headers)
    assert response.status_code == 200, (
        f"GET {SETTINGS} with no credential configured returned {response.status_code}: "
        f"{response.text[:200]}"
    )
    body = response.json()
    assert _llm_status(body) in NOT_CONFIGURED, (
        f"the settings page reports {_llm_status(body)!r} for an unconfigured "
        "language-model credential"
    )
    entry = _llm_credential_entry(body)
    assert str(entry.get("value", "")) != "", (
        "the unconfigured credential shows no placeholder at all, so the page cannot "
        f"state that nothing is configured: {entry}"
    )


def test_ac057_the_status_is_only_ever_connected_or_not_configured(api: TestClient) -> None:
    """AC-057: every credential status the settings page reports is one of the two
    words the criterion allows."""
    _configured_llm_value()
    headers = admin_headers(api)

    response = api.get(SETTINGS, headers=headers)
    assert response.status_code == 200
    body = response.json()
    credentials = body.get("credentials")
    assert isinstance(credentials, list) and credentials, (
        f"the settings page lists no credentials: {str(body)[:300]}"
    )
    unexpected = {
        str(item.get("name")): str(item.get("status"))
        for item in credentials
        if str(item.get("status", "")).strip().lower() not in (CONNECTED, *NOT_CONFIGURED)
    }
    assert not unexpected, (
        f"these credential statuses are neither connected nor not configured: {unexpected}"
    )


def test_ac057_nfr011_the_settings_page_never_names_a_credential_environment_value(
    api: TestClient,
) -> None:
    """AC-057 / NFR-011: the database connection string is masked on the same page,
    so neither credential is ever readable from a screen."""
    headers = admin_headers(api)
    response = api.get(SETTINGS, headers=headers)
    assert response.status_code == 200

    database_url = os.environ.get("DATABASE_URL", "")
    if database_url:
        assert database_url not in response.text, (
            "the settings page shows the raw database connection string"
        )
        password = database_url.rsplit("@", 1)[0].rsplit(":", 1)[-1]
        if password and len(password) > 3:
            assert password not in response.text, (
                "the settings page shows the database password"
            )

    assert any(
        "not-shown" in value.lower() or "mask" in value.lower() or "*" in value
        for value in _strings(response.json())
    ), f"no credential on the settings page is shown as a masked placeholder: {response.text[:300]}"
