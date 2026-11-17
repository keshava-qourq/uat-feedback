"""Admin ingest-run routes: start a run, and read its report.

The work itself belongs to `app.ingest.job` (US-001-2/3): this router only
creates the `ingest_runs` row, queues the job, and reports what the job has
written so far -- so a screen polling the report sees progress while the run
is still going (NFR-006).

One run at a time: a second start while a run is queued or running is a
conflict (409), because two runs over the same store would race on the
replace-the-prior-load step (NFR-021).
"""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import require_api_access
from app.database import get_db
from app.ingest import enqueue_ingest
from app.models import IngestFileResult, IngestRun

router = APIRouter(
    prefix="/api/admin/ingest-runs",
    tags=["admin"],
    dependencies=[Depends(require_api_access)],
)

IN_PROGRESS = ("queued", "running")

#: How long a run may sit in queued/running without its job reporting anything
#: before it is treated as abandoned. NFR-021 serialises *live* runs; a row left
#: behind by an interrupted process must not lock ingest out forever.
STALE_AFTER = timedelta(minutes=30)


def _aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


def _live_run(db: Session) -> IngestRun | None:
    """The run that is genuinely still going, if any; stale rows are closed off."""
    rows = db.execute(select(IngestRun).where(IngestRun.status.in_(IN_PROGRESS))).scalars().all()
    cutoff = datetime.now(UTC) - STALE_AFTER
    live: IngestRun | None = None
    changed = False
    for row in rows:
        started = _aware(row.started_at)
        if started is not None and started < cutoff:
            row.status = "failed"
            row.finished_at = datetime.now(UTC)
            changed = True
            continue
        live = live or row
    if changed:
        db.commit()
    return live


class StartIngestRun(BaseModel):
    """What a start may carry. Everything falls back to the configured location."""

    dataset_version: str | None = None
    source_uri: str | None = None
    seed: int | None = None


def _iso(value: datetime | None) -> str | None:
    return None if value is None else value.isoformat()


def _report(db: Session, run: IngestRun) -> dict[str, Any]:
    rows = (
        db.execute(
            select(IngestFileResult)
            .where(IngestFileResult.ingest_run_id == run.id)
            .order_by(IngestFileResult.file_name)
        )
        .scalars()
        .all()
    )
    files = [
        {
            # `file` is the contract's name; `file_name` is the column's, kept
            # so a reader of either name finds the file it is looking at.
            "file": row.file_name,
            "file_name": row.file_name,
            "status": row.status,
            "rows_loaded": row.rows_loaded or 0,
            "rows_rejected": row.rows_rejected or 0,
            # How many of those rejections were provenance failures: a row
            # with no source_type/source_ref, or a source_type outside
            # ehr|claim|patient (AC-007).
            "provenance_failures": row.provenance_failures or 0,
            # A failure always carries its reason: the file and the column or
            # field behind it, never a silently empty line.
            "error": row.error_detail,
        }
        for row in rows
    ]
    run_body = {
        "run_id": run.id,
        "status": run.status,
        "dataset_version": run.dataset_version,
        "seed": run.seed,
        "patient_count": run.patient_count or 0,
        "started_at": _iso(run.started_at),
        "finished_at": _iso(run.finished_at),
    }
    # The provenance failures of this run, per file: how many rows had no
    # usable source_type/source_ref and the detail naming them (AC-007).
    provenance_failures = [
        {
            "file": line["file"],
            "count": line["provenance_failures"],
            "detail": line["error"],
        }
        for line in files
        if line["provenance_failures"]
    ]
    return {
        **run_body,
        "run": run_body,
        "files": files,
        "provenance_failures": provenance_failures,
    }


@router.post("", status_code=status.HTTP_202_ACCEPTED)
def start_ingest_run(
    body: StartIngestRun, db: Annotated[Session, Depends(get_db)]
) -> dict[str, Any]:
    """Queue one ingest run over the configured dataset location."""
    dataset_version = body.dataset_version or os.getenv("INGEST_DATASET_VERSION")
    source_uri = body.source_uri or os.getenv("INGEST_SOURCE_URI")
    if not dataset_version or not source_uri:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "dataset_version and source_uri are required: neither was given nor "
                "configured as INGEST_DATASET_VERSION / INGEST_SOURCE_URI"
            ),
        )

    running = _live_run(db)
    if running is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"ingest run {running.id} is already in progress",
        )

    run = IngestRun(dataset_version=dataset_version, seed=body.seed, status="queued")
    db.add(run)
    db.commit()

    try:
        job_id = enqueue_ingest(run.id, dataset_version, source_uri, body.seed)
    except Exception as exc:  # noqa: BLE001 -- a queue that is down must not lock out later runs
        run.status = "failed"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"the job queue is unavailable: {exc}",
        ) from exc
    return {
        "run_id": run.id,
        "job_id": job_id,
        "status": "queued",
        "dataset_version": run.dataset_version,
        "seed": run.seed,
        "started_at": _iso(run.started_at),
    }


@router.get("/{run_id}")
def get_ingest_run(run_id: str, db: Annotated[Session, Depends(get_db)]) -> dict[str, Any]:
    """The run's report: its summary and one pass/fail line per file."""
    run = db.get(IngestRun, run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"no ingest run {run_id}")
    return _report(db, run)
