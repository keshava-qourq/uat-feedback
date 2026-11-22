"""The de-duplication check: merged timeline entries against encounter_truth.csv.

The dataset ships a truth file saying which real encounters a patient had.
This check reads those rows back from the `encounter_truth` table the ingest
loaded, rebuilds the merged encounters the timeline shows (the same
`app.dedup` rule the read path uses) and reports, for the active dataset
version:

* `true_encounters` -- how many truth rows were checked;
* `matched_to_one_entry` -- true encounters represented by exactly one merged
  entry;
* `split_into_more_than_one` -- true encounters whose source rows ended up in
  more than one merged entry;
* `merged_in_error` -- source rows that joined a merged entry describing a
  different true encounter;
* `invisible_care` -- true encounters no EHR or claim row describes at all.
  These are counted here and never created as a timeline entry: the product
  only draws what its sources contain (AC-013).

The check never writes: it reads events and truth rows and answers numbers,
so it is safe to run twice.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.dataset import active_dataset_version
from app.dedup import TOLERANCE, group_rows
from app.models import EncounterTruth, Event, Patient

__all__ = ["check_dedup", "run_dedup_check"]

#: The sources a real encounter can be visible in.
VISIBLE_SOURCE_TYPES = ("ehr", "claim")


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


def _nearest_truth(row: Event, truths: list[EncounterTruth]) -> str | None:
    """The true encounter this source row describes, if any is close enough."""
    if row.event_time is None:
        return None
    when = _aware(row.event_time)
    best: tuple[Any, str] | None = None
    for truth in truths:
        distance = abs(_aware(truth.encounter_time) - when)
        if distance <= TOLERANCE and (best is None or distance < best[0]):
            best = (distance, truth.true_encounter_id)
    return None if best is None else best[1]


def _patient_counts(rows: list[Event], truths: list[EncounterTruth]) -> dict[str, int]:
    """The four counts for one patient's events against their truth rows."""
    assigned = {row.id: _nearest_truth(row, truths) for row in rows}
    groups = group_rows(rows)

    # true encounter -> the merged entries that carry at least one of its rows
    entries: dict[str, set[int]] = {truth.true_encounter_id: set() for truth in truths}
    merged_in_error = 0
    for index, group in enumerate(groups):
        truth_ids = [assigned[member.id] for member in group if assigned[member.id]]
        for truth_id in truth_ids:
            entries[truth_id].add(index)
        distinct = sorted(set(truth_ids))
        if len(distinct) > 1:
            # The group describes more than one real encounter: every row
            # beyond the earliest encounter's rows was merged in error.
            earliest = min(
                distinct,
                key=lambda truth_id: _aware(
                    next(t.encounter_time for t in truths if t.true_encounter_id == truth_id)
                ),
            )
            merged_in_error += sum(1 for truth_id in truth_ids if truth_id != earliest)

    counts = {
        "matched_to_one_entry": 0,
        "split_into_more_than_one": 0,
        "merged_in_error": merged_in_error,
        "invisible_care": 0,
    }
    for found in entries.values():
        if not found:
            counts["invisible_care"] += 1
        elif len(found) == 1:
            counts["matched_to_one_entry"] += 1
        else:
            counts["split_into_more_than_one"] += 1
    return counts


def check_dedup(
    db: Session,
    dataset_version: str | None = None,
    progress: Any = None,
) -> dict[str, Any]:
    """The de-duplication report over the loaded cohort. Writes nothing."""
    version = dataset_version or active_dataset_version(db) or ""
    patients = list(
        db.execute(
            select(Patient).where(Patient.dataset_version == version).order_by(Patient.id)
        ).scalars()
    )
    report = {
        "true_encounters": 0,
        "matched_to_one_entry": 0,
        "split_into_more_than_one": 0,
        "merged_in_error": 0,
        "invisible_care": 0,
        "dataset_version": version,
    }
    total = len(patients) or 1
    for done, patient in enumerate(patients, start=1):
        truths = list(
            db.execute(
                select(EncounterTruth)
                .where(EncounterTruth.patient_id == patient.id)
                .order_by(EncounterTruth.encounter_time)
            ).scalars()
        )
        if truths:
            rows = list(
                db.execute(
                    select(Event)
                    .where(
                        Event.patient_id == patient.id,
                        Event.source_type.in_(VISIBLE_SOURCE_TYPES),
                    )
                    .order_by(Event.event_time)
                ).scalars()
            )
            report["true_encounters"] += len(truths)
            for key, value in _patient_counts(rows, truths).items():
                report[key] += value
        if progress is not None:
            progress(round(done * 100 / total, 2))
    return report


def run_dedup_check(dataset_version: str | None = None) -> dict[str, Any]:
    """The RQ job: run the check and report progress through the job's meta."""
    try:
        from rq import get_current_job

        job = get_current_job()
    except Exception:  # noqa: BLE001 -- run outside a worker, there is no job meta
        job = None

    def report_progress(pct: float) -> None:
        if job is None:
            return
        job.meta["progress_pct"] = pct
        job.meta["progress_message"] = f"de-duplication check {pct}% complete"
        job.save_meta()

    report_progress(0.0)
    db = SessionLocal()
    try:
        result = check_dedup(db, dataset_version, progress=report_progress)
    finally:
        db.close()
    report_progress(100.0)
    return result
