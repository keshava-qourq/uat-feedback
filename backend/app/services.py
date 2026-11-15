"""Reachability of the backing services this application depends on.

The approved architecture (docs/sdlc/architecture/README.md) names three:
PostgreSQL 16 (`db`), Redis 7 as the read cache (`cache`) and the same Redis 7
as the job queue (`queue`) -- one Redis instance serving both roles, read from
the one `REDIS_URL` the project's services list provides (see
`ENVIRONMENT.md`). `GET /health` reports all three so a deployment's liveness
probe catches a database or Redis that is down, not just a process that is up.

Every check tolerates the dependency being absent or unreachable -- a fresh
clone with no `.env` has no Postgres and no Redis, and `/health` must still
answer so a developer can tell "nothing is configured yet" from "the process
will not start".
"""

import os

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

_CHECK_TIMEOUT_SECONDS = 2


def _check_database() -> bool:
    url = os.getenv("DATABASE_URL")
    if not url:
        return False
    connect_args = {} if url.startswith("sqlite") else {"connect_timeout": _CHECK_TIMEOUT_SECONDS}
    try:
        engine = create_engine(url, connect_args=connect_args, pool_pre_ping=True)
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        finally:
            engine.dispose()
    except SQLAlchemyError:
        return False


def _check_redis() -> bool:
    url = os.getenv("REDIS_URL")
    if not url:
        return False
    try:
        import redis

        client = redis.from_url(
            url,
            socket_connect_timeout=_CHECK_TIMEOUT_SECONDS,
            socket_timeout=_CHECK_TIMEOUT_SECONDS,
        )
        try:
            return bool(client.ping())
        finally:
            client.close()
    except Exception:  # noqa: BLE001 -- any connection failure means "not reachable"
        return False


def database_reachable() -> bool:
    """Whether the configured Postgres answers right now."""
    return _check_database()


def configured_services() -> dict[str, bool]:
    """Whether each backing service answers right now: `db`, `cache`, `queue`.

    `cache` and `queue` are the same Redis instance (see module docstring), so
    they share one ping -- a second connection would only double-count the
    same failure or success.
    """
    redis_ok = _check_redis()
    return {
        "db": _check_database(),
        "cache": redis_ok,
        "queue": redis_ok,
    }
