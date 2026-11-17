"""Every environment setting this service reads, in one place, with a local default.

The platform always provides `ALLOWED_ORIGINS`, `SECRET_KEY`, `JWT_SECRET_KEY`
and `MEDIA_ROOT` on the deployed API, and `DATABASE_URL`, `REDIS_URL`,
`S3_BUCKET`/`AWS_REGION`, `ANTHROPIC_API_KEY` and `SENDGRID_API_KEY` for the
project's services (see ENVIRONMENT.md). None of them is required to start:
every reader below falls back to something that works on a laptop and in the
unit-test run, so a fresh clone boots and `/health` tells you what is missing
rather than the process refusing to come up.

Read at call time, never snapshotted at import: a test that monkeypatches an
environment variable must see the new value, and a worker process that starts
hours after the web process must read the same environment the platform set.

No credential value is ever logged or returned from here -- `*_configured()`
answers whether a credential exists and nothing else (NFR-011).
"""

from __future__ import annotations

import os
from dataclasses import dataclass

#: Where the SPA runs when nobody has said otherwise (the Vite dev server).
DEFAULT_DEV_ORIGINS: tuple[str, ...] = ("http://localhost:5173", "http://127.0.0.1:5173")

#: The local database a fresh clone falls back to, so `pip install` is enough to run.
DEFAULT_DATABASE_URL = "sqlite:///./app.db"


def _env(name: str, default: str = "") -> str:
    return (os.getenv(name) or default).strip()


@dataclass(frozen=True)
class Settings:
    """A snapshot of the environment, as `get_settings()` read it."""

    database_url: str
    redis_url: str
    allowed_origins: tuple[str, ...]
    secret_key: str
    jwt_secret_key: str
    media_root: str
    s3_bucket: str
    aws_region: str
    anthropic_api_key: str
    sendgrid_api_key: str

    @property
    def anthropic_configured(self) -> bool:
        return bool(self.anthropic_api_key)

    @property
    def sendgrid_configured(self) -> bool:
        return bool(self.sendgrid_api_key)

    @property
    def s3_configured(self) -> bool:
        return bool(self.s3_bucket)


def allowed_origins() -> list[str]:
    """The origins CORS allows: `ALLOWED_ORIGINS` (comma separated), else the dev server.

    The SPA and the API are always on different origins once deployed, so this
    is the only thing standing between the frontend and a blocked request.
    """
    configured = [origin.strip() for origin in _env("ALLOWED_ORIGINS").split(",") if origin.strip()]
    return configured or list(DEFAULT_DEV_ORIGINS)


def database_url() -> str:
    """The SQLAlchemy URL of the database (`postgresql+psycopg://...` when deployed)."""
    return _env("DATABASE_URL") or DEFAULT_DATABASE_URL


def redis_url() -> str:
    """The Redis used for both the read cache and the job queue, or "" when absent.

    Empty is a supported state: the cache degrades to a miss and the queue
    reports itself unavailable rather than the request failing.
    """
    return _env("REDIS_URL")


def shared_api_key() -> str:
    """`SECRET_KEY`: the shared bearer the generated SPA sends. Public -- signs nothing."""
    return _env("API_SECRET_KEY") or _env("SECRET_KEY")


def session_secret() -> str:
    """`JWT_SECRET_KEY`: the private secret that hashes session and link tokens.

    Never `SECRET_KEY`, which is public (it is baked into the frontend bundle).
    Falls back to a fixed development value so a laptop run works; a deployment
    always has the real one.
    """
    return _env("JWT_SECRET_KEY") or "dev-only-session-secret"


def media_root() -> str:
    """`MEDIA_ROOT`: the writable directory that survives redeploys.

    `app.storage` owns the default and the directory's creation; this is here
    so every reader of the name goes through one place.
    """
    from app.storage import DEFAULT_MEDIA_ROOT

    return _env("MEDIA_ROOT") or DEFAULT_MEDIA_ROOT


def get_settings() -> Settings:
    """The environment as it is right now."""
    return Settings(
        database_url=database_url(),
        redis_url=redis_url(),
        allowed_origins=tuple(allowed_origins()),
        secret_key=shared_api_key(),
        jwt_secret_key=session_secret(),
        media_root=media_root(),
        s3_bucket=_env("S3_BUCKET"),
        aws_region=_env("AWS_REGION"),
        anthropic_api_key=_env("ANTHROPIC_API_KEY") or _env("LLM_API_KEY"),
        sendgrid_api_key=_env("SENDGRID_API_KEY"),
    )
