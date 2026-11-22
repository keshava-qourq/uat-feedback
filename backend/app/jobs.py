"""The job queue: one place that knows how work reaches an RQ worker.

The architecture runs the minutes-long work -- dataset ingest, de-duplication,
LLM clue extraction, model training, evaluation and persona warming -- as RQ
jobs on the project's Redis (`REDIS_URL`), so no screen blocks while they run.
This module owns the connection, the queue names and the status shape; a
ticket that adds a job writes the function and calls `enqueue`, and never
builds a Redis client of its own.

Two rules the architecture fixes, and this module keeps:

* **Jobs must be safe to run twice.** Nothing here deduplicates for you -- an
  enqueued job may be retried by the worker or re-submitted by a screen, so a
  job function must be written idempotent (the ingest job, for instance,
  replaces the prior load of its dataset version rather than appending).
* **Redis may be missing.** `enqueue` raises `QueueUnavailable` rather than a
  bare connection error, so a route answers 503 with a readable reason instead
  of a stack trace, and `status` reports "unavailable" rather than raising.
"""

from __future__ import annotations

from typing import Any

from app.config import redis_url

#: The queues this application uses. `ingest` is kept separate so a long dataset
#: load never sits in front of a short interactive job.
QUEUE_INGEST = "ingest"
QUEUE_DEFAULT = "default"
QUEUE_NAMES: tuple[str, ...] = (QUEUE_INGEST, QUEUE_DEFAULT)

#: The kinds `POST /api/admin/jobs` accepts, per the approved API spec.
JOB_KINDS: tuple[str, ...] = (
    "ingest",
    "dedup_check",
    "extraction",
    "training",
    "evaluation",
    "warm_personas",
)

#: An hour: long enough for the ingest of ~572k events, short enough that a
#: wedged job is eventually reaped rather than holding a worker forever.
DEFAULT_JOB_TIMEOUT = 3600


class QueueUnavailable(RuntimeError):
    """Redis is not configured or not reachable, so nothing could be queued."""


def connection():
    """A Redis connection for the queue. Raises `QueueUnavailable` when there is none."""
    url = redis_url()
    if not url:
        raise QueueUnavailable("REDIS_URL is not set: no job queue is configured")
    try:
        import redis

        return redis.from_url(url)
    except QueueUnavailable:
        raise
    except Exception as exc:  # noqa: BLE001 -- any connection failure is the same answer
        raise QueueUnavailable(f"the job queue is unreachable: {exc}") from exc


def get_queue(name: str = QUEUE_DEFAULT):
    """The named RQ queue. Raises `QueueUnavailable` when Redis is not there."""
    try:
        from rq import Queue
    except ImportError as exc:  # pragma: no cover -- rq is a declared dependency
        raise QueueUnavailable(f"rq is not installed: {exc}") from exc
    return Queue(name, connection=connection(), default_timeout=DEFAULT_JOB_TIMEOUT)


def enqueue(func, *args: Any, queue_name: str = QUEUE_DEFAULT, **kwargs: Any) -> str:
    """Queue `func(*args, **kwargs)` and return the RQ job id.

    `func` must be importable by the worker process by its module path -- the
    worker runs this same codebase, so a module-level function in `app.*` is
    always reachable. Raises `QueueUnavailable` when Redis is not there.
    """
    job_timeout = kwargs.pop("job_timeout", DEFAULT_JOB_TIMEOUT)
    job = get_queue(queue_name).enqueue(func, *args, job_timeout=job_timeout, **kwargs)
    return job.id


def status(job_id: str) -> dict[str, Any]:
    """What a progress screen needs: `{job_id, status, progress_pct, result}`.

    `status` is RQ's own ("queued", "started", "finished", "failed"), or
    "unavailable" when the queue cannot be reached and "unknown" when the id
    is not (or is no longer) on it. Never raises: a polling screen that cannot
    reach Redis should show "unavailable", not an error page.
    """
    unknown = {"job_id": job_id, "status": "unknown", "progress_pct": None, "result": None}
    try:
        from rq.job import Job

        job = Job.fetch(job_id, connection=connection())
    except QueueUnavailable:
        return {**unknown, "status": "unavailable"}
    except Exception:  # noqa: BLE001 -- an id RQ does not know is "unknown", not an error
        return unknown
    meta = job.meta or {}
    return {
        "job_id": job.id,
        # The kind the route queued it as, stored on the job's meta.
        "kind": meta.get("kind"),
        # str(): RQ answers with a JobStatus enum, and a response body should
        # carry the plain word a screen compares against.
        "status": str(job.get_status(refresh=False).value),
        # A job function reports progress by writing `job.meta["progress_pct"]`
        # and `job.meta["progress_message"]`; absent, they are simply None.
        "progress_pct": meta.get("progress_pct"),
        "progress_message": meta.get("progress_message"),
        "result": job.result,
    }


def available() -> bool:
    """Whether the queue's Redis answers right now. For `/health`."""
    try:
        client = connection()
    except QueueUnavailable:
        return False
    try:
        return bool(client.ping())
    except Exception:  # noqa: BLE001
        return False
    finally:
        try:
            client.close()
        except Exception:  # noqa: BLE001
            pass
