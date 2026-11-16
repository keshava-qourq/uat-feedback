"""The Anthropic (Claude) client, and the one place that knows whether it exists.

The architecture's `llm` component wraps the Anthropic API for clue extraction
and for the cited clinician/patient text. What belongs here is only the seam:
how the client is built, which model it talks to, and how the rest of the app
asks whether the credential is there. The prompts, the structured findings and
the citation shapes are each a development ticket's work (US-015, US-016,
US-017) and are deliberately absent.

Degrading is a requirement, not an accident: with no `ANTHROPIC_API_KEY` the
app must still run and report "not configured" on the settings screen, and the
features that would have called Claude fall back to structured-only output.
`is_configured()` is how a caller asks; `get_client()` returns None rather than
raising, so no code path has to guard with a try/except to stay up.

Tests never call the real API: the sandbox has no key for it and a unit test
must not depend on a network. A test either checks `is_configured()` is False,
or substitutes the client this module returns.
"""

from __future__ import annotations

from typing import Any

from app.config import get_settings

#: Overridable with `ANTHROPIC_MODEL`; the default is the current Sonnet line.
DEFAULT_MODEL = "claude-sonnet-4-5"

STATUS_CONNECTED = "connected"
STATUS_NOT_CONFIGURED = "not configured"


def is_configured() -> bool:
    """Whether an Anthropic credential is present. Never reveals its value."""
    return get_settings().anthropic_configured


def model_name() -> str:
    """The model every call in this application uses."""
    import os

    return (os.getenv("ANTHROPIC_MODEL") or "").strip() or DEFAULT_MODEL


def get_client() -> Any | None:
    """An `anthropic.Anthropic`, or None when no credential is configured.

    Built per call rather than cached at import, so a process that starts
    before the platform sets the variable still picks it up, and a test can
    set and unset it freely.
    """
    settings = get_settings()
    if not settings.anthropic_configured:
        return None
    try:
        import anthropic

        return anthropic.Anthropic(api_key=settings.anthropic_api_key)
    except Exception:  # noqa: BLE001 -- an unusable client is "not configured", not a crash
        return None


def connection_status() -> str:
    """Either "connected" or "not configured", for `GET /api/admin/settings`.

    Reports whether the credential is there, not whether a call would succeed:
    the settings screen must answer instantly and must never spend a token to
    draw itself.
    """
    return STATUS_CONNECTED if is_configured() else STATUS_NOT_CONFIGURED
