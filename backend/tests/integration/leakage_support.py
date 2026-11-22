"""Shared helpers for the leakage-guarantee acceptance tests (US-003-4).

The cohort is built the way the behaviour rules and NFR-021 require: one
module-scoped ingest of a leakage fixture drop through the real API, tolerating
a 409 when another run is already in flight, and otherwise reusing whatever
cohort GET /api/worklist already serves. Nothing is written into the database
by hand and no application module is imported to read data.
"""

from __future__ import annotations

import os
import re
import uuid
from datetime import date, datetime
from typing import Any

from fastapi.testclient import TestClient

from tests.integration import fixtures_dataset as fx
from tests.integration.conftest import wait_for_run
from tests.integration.fixtures_leakage import LeakageDrop

INGEST_START = "/api/admin/ingest-runs"
WORKLIST = "/api/worklist"

#: Where a patient's evaluation cutoff may arrive in a payload.
CUTOFF_KEYS = ("cutoff_date", "eval_cutoff_date", "evaluation_cutoff_date", "cutoff")

#: Keys whose value is the date of an item in a case's evidence or timeline.
ITEM_DATE_KEYS = ("item_time", "item_date", "event_time", "occurred_at", "note_time", "date")

#: An object is an "item" of a case when it carries one of these.
ITEM_MARKERS = ("item_time", "item_date", "event_time", "event_type", "source_ref")

_DATE = re.compile(r"^(\d{4}-\d{2}-\d{2})")


def objects(payload: Any) -> list[dict]:
    found: list[dict] = []
    if isinstance(payload, dict):
        found.append(payload)
        for value in payload.values():
            found.extend(objects(value))
    elif isinstance(payload, list):
        for item in payload:
            found.extend(objects(item))
    return found


def strings(payload: Any) -> list[str]:
    if isinstance(payload, str):
        return [payload]
    if isinstance(payload, dict):
        out: list[str] = []
        for key, value in payload.items():
            out.append(str(key))
            out.extend(strings(value))
        return out
    if isinstance(payload, list):
        out = []
        for item in payload:
            out.extend(strings(item))
        return out
    return [] if payload is None else [str(payload)]


def as_date(value: Any) -> date | None:
    """The calendar date a value carries, or None when it carries none."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if not isinstance(value, str):
        return None
    match = _DATE.match(value.strip())
    if not match:
        return None
    try:
        return date.fromisoformat(match.group(1))
    except ValueError:
        return None


def cutoff_of(payload: Any) -> date | None:
    """The evaluation cutoff a payload states, if it states one."""
    for obj in objects(payload):
        for key in CUTOFF_KEYS:
            found = as_date(obj.get(key))
            if found is not None:
                return found
    return None


def post_cutoff_items(payload: Any, cutoff: date) -> list[tuple[str, str, str]]:
    """Every item in `payload` dated on or after `cutoff`.

    Returns `(the key that carried the date, the date, a description of the
    item)` so an assertion message names the offending field and item date.
    Undated items -- family history is the only allowed one -- are skipped.
    """
    offenders: list[tuple[str, str, str]] = []
    for obj in objects(payload):
        if not any(marker in obj for marker in ITEM_MARKERS):
            continue
        for key in ITEM_DATE_KEYS:
            if key not in obj:
                continue
            when = as_date(obj.get(key))
            if when is not None and when >= cutoff:
                label = str(obj.get("display") or obj.get("event_type") or obj.get("id") or obj)
                offenders.append((key, when.isoformat(), label[:120]))
    return offenders


def drain_ingest_queue() -> None:
    """Run whatever is on the ingest queue, as the deployed RQ worker would."""
    import redis
    from rq import Queue, SimpleWorker

    connection = redis.from_url(os.environ["REDIS_URL"])
    queue = Queue("ingest", connection=connection)
    SimpleWorker([queue], connection=connection).work(burst=True)


_STATE: dict[str, Any] = {}


def worklist_rows(api: TestClient, admin: dict[str, str]) -> list[dict]:
    response = api.get(WORKLIST, headers=admin)
    assert response.status_code == 200, (
        f"GET {WORKLIST} returned {response.status_code}: {response.text[:200]}"
    )
    return [
        row
        for row in objects(response.json())
        if row.get("patient_id") and row.get("dataset_patient_id")
    ]


def leakage_cohort(api: TestClient, admin: dict[str, str]) -> LeakageDrop:
    """The leakage fixture cohort, ingested once per module through the real API.

    Ingest is serialised one run at a time (NFR-021) and the sandbox database
    is shared, so a 409 is tolerated: the queue is drained and the start tried
    once more before the criterion is allowed to fail.
    """
    existing = _STATE.get("drop")
    if isinstance(existing, LeakageDrop):
        return existing

    drop = LeakageDrop(uuid.uuid4().hex[:8])
    source_uri, _prefix = fx.upload_fixture_set(drop.files())
    for attempt in range(2):
        drain_ingest_queue()
        response = api.post(
            INGEST_START,
            headers=admin,
            json={
                "dataset_version": f"qa-leak-{drop.suffix}",
                "source_uri": source_uri,
                "seed": 29,
            },
        )
        drain_ingest_queue()
        if response.status_code == 409 and attempt == 0:
            continue
        assert response.status_code in (200, 202), (
            f"starting the leakage cohort's ingest run returned {response.status_code}: "
            f"{response.text[:300]}"
        )
        wait_for_run(api, admin, response.json()["run_id"])
        break
    _STATE["drop"] = drop
    return drop


def patient_uuids(api: TestClient, admin: dict[str, str], drop: LeakageDrop) -> dict[str, str]:
    """dataset patient id -> internal uuid, for this drop, read from the worklist."""
    wanted = set(drop.patient_ids)
    found = {
        str(row["dataset_patient_id"]): str(row["patient_id"])
        for row in worklist_rows(api, admin)
        if row.get("dataset_patient_id") in wanted
    }
    assert found, (
        "none of the leakage fixture patients "
        f"{sorted(wanted)} are visible through GET {WORKLIST}, so the leakage "
        "guarantee cannot be checked against a cohort with known ground truth"
    )
    return found


def rendered_reads(api: TestClient, admin: dict[str, str], patient_uuid: str) -> dict[str, Any]:
    """Every read route that renders this patient, route -> payload (200s only)."""
    payloads: dict[str, Any] = {}
    for path in (
        f"/api/cases/{patient_uuid}/timeline",
        f"/api/cases/{patient_uuid}",
        f"/api/cases/{patient_uuid}/evidence",
        f"/api/cases/{patient_uuid}/criteria",
    ):
        response = api.get(path, headers=admin)
        if response.status_code == 200:
            payloads[path] = response.json()
    return payloads
