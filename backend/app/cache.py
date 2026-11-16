"""The read cache: Redis 7, and nothing that breaks when it is not there.

The architecture keeps computed worklists, persona bundles, assembled
timelines, generated narrative text and the latest evaluation numbers warm so
a repeat open is fast enough for the demo budget. Every key here is
disposable: a miss, an unreachable Redis or no `REDIS_URL` at all means the
caller recomputes, which is slower and never wrong. No failure from this
module ever reaches a request -- `get_json` returns None and `set_json`
returns False instead of raising.

Values are stored as JSON with a TTL, so nothing lives forever and nothing
depends on a Python pickle surviving a deployment.
"""

from __future__ import annotations

import json
from typing import Any

from app.config import redis_url

#: Prefixed so this application's keys never collide with the job queue's own.
KEY_PREFIX = "cache:"

#: Long enough that a demo stays warm, short enough that stale data expires.
DEFAULT_TTL_SECONDS = 900


def _client():
    """A Redis client, or None when Redis is not configured or not reachable."""
    url = redis_url()
    if not url:
        return None
    try:
        import redis

        return redis.from_url(url, socket_connect_timeout=2, socket_timeout=2)
    except Exception:  # noqa: BLE001 -- an unusable cache is a miss, never an error
        return None


def key(*parts: Any) -> str:
    """One cache key from its parts: `cache:worklist:<clinician_id>`."""
    return KEY_PREFIX + ":".join(str(part) for part in parts)


def get_json(name: str) -> Any | None:
    """The decoded value stored under `name`, or None on any miss or failure."""
    client = _client()
    if client is None:
        return None
    try:
        raw = client.get(name)
    except Exception:  # noqa: BLE001 -- treat an unreachable cache as a miss
        return None
    finally:
        _close(client)
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except ValueError:
        return None


def set_json(name: str, value: Any, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> bool:
    """Store `value` under `name` for `ttl_seconds`. False when it could not be stored."""
    client = _client()
    if client is None:
        return False
    try:
        client.set(name, json.dumps(value, default=str), ex=ttl_seconds)
        return True
    except Exception:  # noqa: BLE001 -- a cache that will not take a write is not an error
        return False
    finally:
        _close(client)


def delete(*names: str) -> None:
    """Drop these keys. Used after a rescore or a pack change invalidates them."""
    if not names:
        return
    client = _client()
    if client is None:
        return
    try:
        client.delete(*names)
    except Exception:  # noqa: BLE001 -- nothing to do if the cache cannot be reached
        return
    finally:
        _close(client)


def delete_prefix(prefix: str) -> int:
    """Drop every key beginning with `prefix`; returns how many were dropped.

    Scans rather than `KEYS`, so a large keyspace is never blocked.
    """
    client = _client()
    if client is None:
        return 0
    dropped = 0
    try:
        for found in client.scan_iter(match=f"{prefix}*", count=500):
            dropped += int(client.delete(found) or 0)
    except Exception:  # noqa: BLE001 -- a partial sweep still leaves correct (slower) reads
        return dropped
    finally:
        _close(client)
    return dropped


def available() -> bool:
    """Whether the cache answers right now. For `/health` and the settings screen."""
    client = _client()
    if client is None:
        return False
    try:
        return bool(client.ping())
    except Exception:  # noqa: BLE001
        return False
    finally:
        _close(client)


def _close(client) -> None:
    try:
        client.close()
    except Exception:  # noqa: BLE001 -- closing a dead connection is not worth an error
        pass
