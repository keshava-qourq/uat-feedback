"""US-017-1 / AC-056, AC-057, NFR-011: the LLM credential is configuration only.

Three things are proven here:

* the credential is read from configuration at call time through `app.config`,
  with no default or placeholder anywhere;
* a deliberately logged credential value never reaches a log line, including
  exception text from a failed Anthropic call;
* nothing shaped like a credential value is committed to this repository.
"""

from __future__ import annotations

import json
import logging
import re
import secrets
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import config, llm
from app.log_redaction import MASK, install_credential_filter, redact

REPO_ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(autouse=True)
def _clean_llm_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)


# ------------------------------------------------------------------ AC-056: config


def test_ac056_the_credential_is_read_from_anthropic_api_key_at_call_time(
    monkeypatch: pytest.MonkeyPatch,
):
    assert config.llm_api_key() == ""
    assert config.llm_configured() is False
    assert llm.is_configured() is False

    key = secrets.token_urlsafe(24)
    monkeypatch.setenv("ANTHROPIC_API_KEY", key)

    assert config.llm_api_key() == key
    assert config.llm_configured() is True
    assert llm.is_configured() is True


def test_ac056_llm_api_key_is_accepted_as_the_generic_name(monkeypatch: pytest.MonkeyPatch):
    key = secrets.token_urlsafe(24)
    monkeypatch.setenv("LLM_API_KEY", key)

    assert config.llm_api_key() == key
    assert config.get_settings().anthropic_configured is True


def test_ac056_there_is_no_default_or_placeholder_credential():
    assert config.llm_api_key() == ""
    assert config.get_settings().anthropic_api_key == ""
    assert llm.get_client() is None


# ----------------------------------------------------------------- AC-056: logging


def test_ac056_a_deliberately_logged_key_is_redacted(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
):
    key = secrets.token_urlsafe(24)
    monkeypatch.setenv("ANTHROPIC_API_KEY", key)
    install_credential_filter()
    logger = logging.getLogger("test.credentials")

    with caplog.at_level(logging.INFO, logger="test.credentials"):
        logger.info("calling Anthropic with api_key=%s", key)

    written = "\n".join(record.getMessage() for record in caplog.records)
    assert key not in written
    assert MASK in written


def test_ac056_exception_text_from_a_failed_anthropic_call_is_redacted(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
):
    key = secrets.token_urlsafe(24)
    monkeypatch.setenv("ANTHROPIC_API_KEY", key)
    install_credential_filter()
    logger = logging.getLogger("test.credentials.exception")

    with caplog.at_level(logging.ERROR, logger="test.credentials.exception"):
        try:
            raise RuntimeError(f"401 from Anthropic for key {key}")
        except RuntimeError:
            logger.exception("the Anthropic call failed")

    record = caplog.records[-1]
    rendered = logging.Formatter().format(record)
    assert key not in rendered
    assert MASK in rendered


def test_ac056_the_database_connection_string_is_redacted_the_same_way(
    monkeypatch: pytest.MonkeyPatch,
):
    url = f"postgresql+psycopg://user:{secrets.token_urlsafe(12)}@host:5432/db"
    monkeypatch.setenv("DATABASE_URL", url)

    assert url not in redact(f"connecting to {url}")


# --------------------------------------------------------- AC-057: masked reporting


def test_ac057_nfr011_settings_mask_both_credentials_and_report_their_status(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
):
    key = secrets.token_urlsafe(24)
    url = f"postgresql+psycopg://user:{secrets.token_urlsafe(12)}@host:5432/db"
    monkeypatch.setenv("ANTHROPIC_API_KEY", key)
    monkeypatch.setenv("DATABASE_URL", url)
    monkeypatch.setenv("SECRET_KEY", secrets.token_urlsafe(16))
    bearer = config.shared_api_key()

    body = client.get("/api/admin/settings", headers={"Authorization": f"Bearer {bearer}"}).json()

    assert body["llm"]["status"] == "connected"
    credentials = {entry["name"]: entry for entry in body["credentials"]}
    assert credentials["llm"] == {"name": "llm", "status": "connected", "value": "not-shown"}
    assert credentials["database"]["value"] == "not-shown"
    raw = json.dumps(body)
    assert key not in raw
    assert url not in raw


def test_ac057_settings_report_not_configured_with_no_llm_credential(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setenv("SECRET_KEY", secrets.token_urlsafe(16))
    bearer = config.shared_api_key()

    body = client.get("/api/admin/settings", headers={"Authorization": f"Bearer {bearer}"}).json()

    assert body["llm"] == {"status": "not-configured"}
    credentials = {entry["name"]: entry for entry in body["credentials"]}
    assert credentials["llm"]["status"] == "not-configured"
    assert credentials["llm"]["value"] == "not-shown"


# ------------------------------------------------- AC-056: nothing committed anywhere

#: Directories a scan of the working tree must never descend into.
SKIP_DIRECTORIES = {
    ".git",
    ".venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    "dist",
    "build",
    "coverage",
    "test-results",
    ".mypy_cache",
    "media",
}

SKIP_SUFFIXES = {".lock", ".png", ".jpg", ".jpeg", ".gif", ".ico", ".woff", ".woff2", ".pdf"}

#: Things that are shaped like a committed credential value.
CREDENTIAL_PATTERNS = (
    # An Anthropic key, whatever name it is assigned to.
    re.compile(r"sk-ant-[A-Za-z0-9_\-]{8,}"),
    # A SendGrid key.
    re.compile(r"SG\.[A-Za-z0-9_\-]{16,}"),
    # A credential setting assigned a non-empty literal. The names are matched
    # case-sensitively: an environment variable is upper case, while the lower
    # case spelling is a Python identifier reading one.
    re.compile(
        r"\b(ANTHROPIC_API_KEY|LLM_API_KEY|SENDGRID_API_KEY|JWT_SECRET_KEY|"
        r"BOOTSTRAP_ADMIN_PASSWORD|SMOKE_TEST_PASSWORD|AWS_SECRET_ACCESS_KEY)\b"
        r"\s*[=:]\s*[\"'][A-Za-z0-9_\-/+.]{8,}"
    ),
    # A connection string carrying a literal password -- not a `{...}` run-time
    # interpolation and not a `<placeholder>` in the documentation.
    re.compile(r"(?i)postgres(?:ql)?(?:\+\w+)?://[^\s\"'/{<]+:[^\s\"'@/{}<>]{4,}@"),
)


def _scanned_files() -> list[Path]:
    found: list[Path] = []
    for path in REPO_ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRECTORIES for part in path.parts):
            continue
        if path.suffix.lower() in SKIP_SUFFIXES:
            continue
        # .env.example carries the setting names with empty placeholders only.
        if path.name == ".env.example":
            continue
        # This file holds the patterns themselves.
        if path.resolve() == Path(__file__).resolve():
            continue
        found.append(path)
    return found


def test_ac056_no_credential_value_is_committed_anywhere_in_the_repository():
    hits: list[str] = []
    for path in _scanned_files():
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for pattern in CREDENTIAL_PATTERNS:
            for match in pattern.finditer(text):
                line = text[: match.start()].count("\n") + 1
                hits.append(f"{path.relative_to(REPO_ROOT)}:{line}: {pattern.pattern[:40]}")

    assert hits == [], "credential-shaped values are committed: " + "; ".join(hits)
