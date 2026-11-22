"""Credential redaction for every log line this service emits (NFR-011, AC-056).

A credential reaches the process only as deployment configuration. Nothing may
write one into a log: not a debug line, not an exception text from a failed
Anthropic call whose message echoes the key it was given.

The guarantee is applied where a log record is *made*, not where it is
written: `install_credential_filter` installs a record factory that masks
every configured credential value in the record's message, its arguments and
its exception text. A handler added later, a library logger nobody configured,
a traceback rendered by uvicorn's own formatter -- all of them see the masked
record, because there is only one place a record can come from.

The same logic is also exposed as `CredentialFilter`, so a handler can carry
it directly.

Values are read fresh for every record rather than snapshotted, so a process
that picks up its configuration late is still covered.
"""

from __future__ import annotations

import logging
import os

__all__ = [
    "MASK",
    "MIN_LENGTH",
    "SECRET_SETTINGS",
    "CredentialFilter",
    "install_credential_filter",
    "redact",
    "redact_record",
]

#: What a credential is shown as once blanked out.
MASK = "***"

#: The settings whose values are credentials. Their *names* are safe to write
#: down; their values never appear anywhere in this repository.
SECRET_SETTINGS: tuple[str, ...] = (
    "ANTHROPIC_API_KEY",
    "LLM_API_KEY",
    "DATABASE_URL",
    "SENDGRID_API_KEY",
    "JWT_SECRET_KEY",
    "BOOTSTRAP_ADMIN_PASSWORD",
    "SMOKE_TEST_PASSWORD",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_SESSION_TOKEN",
)

#: Shorter than this and a "value" is too generic to blank out safely.
MIN_LENGTH = 8


def _secret_values() -> list[str]:
    """Every configured credential value, longest first so a prefix cannot leak."""
    values = {
        value
        for name in SECRET_SETTINGS
        if len(value := (os.getenv(name) or "").strip()) >= MIN_LENGTH
    }
    return sorted(values, key=len, reverse=True)


def redact(text: str) -> str:
    """`text` with every configured credential value masked."""
    for value in _secret_values():
        text = text.replace(value, MASK)
    return text


def redact_record(record: logging.LogRecord) -> logging.LogRecord:
    """Mask every configured credential value in this record, in place."""
    if isinstance(record.msg, str):
        record.msg = redact(record.msg)
    if record.args:
        if isinstance(record.args, dict):
            record.args = {
                key: redact(value) if isinstance(value, str) else value
                for key, value in record.args.items()
            }
        else:
            record.args = tuple(
                redact(value) if isinstance(value, str) else value for value in record.args
            )
    if record.exc_info:
        text = record.exc_text or logging.Formatter().formatException(record.exc_info)
        record.exc_text = redact(text)
        # The rendered text is kept; the live exception is dropped so no
        # formatter can re-render the unmasked traceback.
        record.exc_info = None
    elif record.exc_text:
        record.exc_text = redact(record.exc_text)
    return record


class CredentialFilter(logging.Filter):
    """Masks any configured credential value in a record before it is written."""

    def filter(self, record: logging.LogRecord) -> bool:
        redact_record(record)
        return True


def install_credential_filter() -> None:
    """Make every log record this process produces credential-free."""
    factory = logging.getLogRecordFactory()
    if getattr(factory, "_redacts_credentials", False):
        return

    def redacting_factory(*args, **kwargs) -> logging.LogRecord:
        return redact_record(factory(*args, **kwargs))

    redacting_factory._redacts_credentials = True  # type: ignore[attr-defined]
    logging.setLogRecordFactory(redacting_factory)
