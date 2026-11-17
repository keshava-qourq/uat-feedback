"""Outbound email through SendGrid: the invite and password-set links, only.

The architecture sends exactly one kind of mail -- a tokenised link to a
patient or a clinical advisor. This module owns the seam: whether SendGrid is
configured, how the client is built, and one `send` that reports success
rather than raising. The message bodies are templated with Jinja2 by whichever
ticket issues the link (US-026, US-031, US-032); none is written here.

Two rules this keeps:

* **Never a blocker.** With no `SENDGRID_API_KEY` the invite is still created
  and its link still returned in the response body -- `send` answers False and
  the caller reports "not emailed", exactly as `send_email: false` would.
  A proof-of-concept run with no mail credential must still issue invites.
* **Never a fake.** With no credential this sends nothing at all; it does not
  pretend to have sent, and it never points at a stand-in SMTP host. A test
  asserts on the False, or substitutes the client.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from app.config import get_settings

logger = logging.getLogger(__name__)

STATUS_CONNECTED = "connected"
STATUS_NOT_CONFIGURED = "not configured"

#: Overridable with `EMAIL_FROM`; a deployment sets its own verified sender.
DEFAULT_FROM_ADDRESS = "no-reply@example.invalid"


@dataclass(frozen=True)
class SendResult:
    """What `send` answers: whether it went, and why it did not."""

    sent: bool
    status_code: int | None = None
    reason: str | None = None

    def __bool__(self) -> bool:
        return self.sent


def is_configured() -> bool:
    """Whether a SendGrid credential is present. Never reveals its value."""
    return get_settings().sendgrid_configured


def from_address() -> str:
    import os

    return (os.getenv("EMAIL_FROM") or "").strip() or DEFAULT_FROM_ADDRESS


def get_client() -> Any | None:
    """A `sendgrid.SendGridAPIClient`, or None when no credential is configured."""
    settings = get_settings()
    if not settings.sendgrid_configured:
        return None
    try:
        import sendgrid

        return sendgrid.SendGridAPIClient(api_key=settings.sendgrid_api_key)
    except Exception:  # noqa: BLE001 -- an unusable client is "not configured", not a crash
        return None


def send(*, to: str, subject: str, html: str, text: str | None = None) -> SendResult:
    """Send one message. Returns a falsey `SendResult` instead of raising.

    A caller that must tell the user whether the mail went reads `.sent`; a
    caller for which mail is a nicety ignores the result entirely.
    """
    client = get_client()
    if client is None:
        return SendResult(sent=False, reason="SendGrid is not configured")
    try:
        from sendgrid.helpers.mail import Mail

        message = Mail(
            from_email=from_address(),
            to_emails=to,
            subject=subject,
            plain_text_content=text,
            html_content=html,
        )
        response = client.send(message)
        code = int(getattr(response, "status_code", 0) or 0)
        if 200 <= code < 300:
            return SendResult(sent=True, status_code=code)
        return SendResult(sent=False, status_code=code, reason=f"SendGrid answered {code}")
    except Exception as exc:  # noqa: BLE001 -- a failed send is reported, never raised
        logger.warning("could not send email: %s", exc)
        return SendResult(sent=False, reason=str(exc))


def connection_status() -> str:
    """Either "connected" or "not configured", for `GET /api/admin/settings`."""
    return STATUS_CONNECTED if is_configured() else STATUS_NOT_CONFIGURED
