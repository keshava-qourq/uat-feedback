"""The background worker's entrypoint: `python -m app.worker`.

The architecture runs the worker as a second container from this same image
and this same codebase, so every job function a ticket writes under `app.*` is
importable here with no packaging step. It consumes the queues
`app.jobs.QUEUE_NAMES` names and nothing else.

`SimpleWorker` (no fork) is used when `RQ_WORKER_CLASS=simple` is set, which a
container with one process per job and a platform that restarts it wants;
the default forking worker is otherwise kept, because it isolates one job's
crash from the next.
"""

from __future__ import annotations

import logging
import os
import sys

from app.jobs import QUEUE_NAMES, QueueUnavailable, connection

logger = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> int:
    """Run a worker until it is stopped. Returns a process exit code."""
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    queue_names = list(argv or []) or list(QUEUE_NAMES)
    try:
        redis_connection = connection()
    except QueueUnavailable as exc:
        logger.error("%s", exc)
        return 1

    from rq import Queue, SimpleWorker, Worker

    worker_class = SimpleWorker if os.getenv("RQ_WORKER_CLASS", "").lower() == "simple" else Worker
    queues = [Queue(name, connection=redis_connection) for name in queue_names]
    logger.info("worker starting on queues: %s", ", ".join(queue_names))
    # burst=True drains what is queued and exits -- used by the tests and by a
    # one-shot run; the deployed worker runs with it unset and stays up.
    worker_class(queues, connection=redis_connection).work(
        burst=os.getenv("RQ_BURST", "").lower() in {"1", "true", "yes"}
    )
    return 0


if __name__ == "__main__":  # pragma: no cover -- exercised as a process, not imported
    sys.exit(main(sys.argv[1:]))
