"""Shared helpers for the de-duplication acceptance tests (US-004-4).

The cohort is built the way the behaviour rules and NFR-021 require: one
module-scoped ingest of a de-duplication fixture drop through the real API,
tolerating a 409 when another run is already in flight. Nothing is written into
the database by hand and no application module is imported to read data.

The de-duplication check itself is run the way the contract says a screen runs
it: POST /api/admin/jobs {"kind": "dedup_check"} and then polling
GET /api/admin/jobs/{job_id} until the job reaches a terminal status.
"""

from __future__ import annotations

import os
import time
import uuid
from typing import Any

from fastapi.testclient import TestClient

from tests.integration import fixtures_dataset as fx
from tests.integration.conftest import wait_for_run
from tests.integration.fixtures_dedup import DedupDrop

INGEST_START = "/api/admin/ingest-runs"
JOBS = "/api/admin/jobs"
WORKLIST = "/api/worklist"

TERMINAL = {"finished", "completed", "complete", "succeeded", "success", "failed", "error"}

#: Where an item's source tag(s) may arrive in a timeline entry.
SOURCE_KEYS = ("sources", "source_types", "source_tags", "contributing_sources", "source_type")


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


def source_tags(item: dict) -> set[str]:
    """Every source tag a timeline entry carries, however it spells them."""
    tags: set[str] = set()
    for key in SOURCE_KEYS:
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            tags.add(value.strip().lower())
        elif isinstance(value, list | tuple):
            for entry in value:
                if isinstance(entry, str):
                    tags.add(entry.strip().lower())
                elif isinstance(entry, dict):
                    for inner in ("source_type", "type", "source", "name"):
                        if isinstance(entry.get(inner), str):
                            tags.add(str(entry[inner]).strip().lower())
    return {tag for tag in tags if tag}


def drain_queues() -> None:
    """Run whatever is on either queue, as the deployed RQ worker would."""
    import redis
    from rq import Queue, SimpleWorker

    connection = redis.from_url(os.environ["REDIS_URL"])
    queues = [Queue(name, connection=connection) for name in ("ingest", "default")]
    SimpleWorker(queues, connection=connection).work(burst=True)


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


def dedup_cohort(api: TestClient, admin: dict[str, str]) -> DedupDrop:
    """The de-duplication fixture cohort, ingested once per module through the
    real API. A 409 (NFR-021 serialises ingest) is tolerated once."""
    existing = _STATE.get("drop")
    if isinstance(existing, DedupDrop):
        return existing

    drop = DedupDrop(uuid.uuid4().hex[:8])
    source_uri, _prefix = fx.upload_fixture_set(drop.files())
    for attempt in range(2):
        drain_queues()
        response = api.post(
            INGEST_START,
            headers=admin,
            json={
                "dataset_version": drop.dataset_version,
                "source_uri": source_uri,
                "seed": 31,
            },
        )
        drain_queues()
        if response.status_code == 409 and attempt == 0:
            continue
        assert response.status_code in (200, 202), (
            f"starting the de-duplication cohort's ingest run returned "
            f"{response.status_code}: {response.text[:300]}"
        )
        wait_for_run(api, admin, response.json()["run_id"])
        break
    _STATE["drop"] = drop
    return drop


def patient_uuids(api: TestClient, admin: dict[str, str], drop: DedupDrop) -> dict[str, str]:
    """dataset patient id -> internal uuid for this drop, read from the worklist."""
    wanted = set(drop.patient_ids)
    found = {
        str(row["dataset_patient_id"]): str(row["patient_id"])
        for row in worklist_rows(api, admin)
        if row.get("dataset_patient_id") in wanted
    }
    assert set(found) == wanted, (
        f"these de-duplication fixture patients are not visible through GET {WORKLIST}, "
        f"so the de-duplication of their encounters cannot be checked: "
        f"{sorted(wanted - set(found))}"
    )
    return found


def timeline_items(api: TestClient, admin: dict[str, str], patient_uuid: str) -> list[dict]:
    response = api.get(f"/api/cases/{patient_uuid}/timeline", headers=admin)
    assert response.status_code == 200, (
        f"GET /api/cases/{patient_uuid}/timeline returned {response.status_code}: "
        f"{response.text[:300]}"
    )
    items = response.json().get("items")
    assert isinstance(items, list), (
        f"the case timeline for patient {patient_uuid} carries no items list: "
        f"{response.text[:300]}"
    )
    return items


def start_dedup_check(api: TestClient, admin: dict[str, str]) -> dict:
    """POST /api/admin/jobs {"kind": "dedup_check"} -> 202 {job_id, kind, status}."""
    response = api.post(JOBS, headers=admin, json={"kind": "dedup_check"})
    assert response.status_code == 202, (
        f"POST {JOBS} {{'kind': 'dedup_check'}} returned {response.status_code}, not 202: "
        f"{response.text[:300]}"
    )
    body = response.json()
    assert body.get("job_id"), f"the queued job carries no job_id: {str(body)[:300]}"
    assert body.get("kind") == "dedup_check", (
        f"the queued job reports kind {body.get('kind')!r}, not 'dedup_check'"
    )
    assert body.get("status"), f"the queued job carries no status: {str(body)[:300]}"
    return body


def wait_for_job(
    api: TestClient, admin: dict[str, str], job_id: str, timeout: float = 120.0
) -> dict:
    """Poll GET /api/admin/jobs/{job_id} until the job reaches a terminal status."""
    deadline = time.monotonic() + timeout
    body: dict = {}
    while time.monotonic() < deadline:
        drain_queues()
        response = api.get(f"{JOBS}/{job_id}", headers=admin)
        assert response.status_code == 200, (
            f"GET {JOBS}/{job_id} returned {response.status_code}: {response.text[:300]}"
        )
        body = response.json()
        if str(body.get("status", "")).lower() in TERMINAL:
            return body
        time.sleep(1.0)
    raise AssertionError(
        f"the de-duplication check job {job_id} did not finish within {timeout:.0f}s; "
        f"last status: {str(body)[:300]}"
    )


def dedup_report(api: TestClient, admin: dict[str, str]) -> dict:
    """Run the check once for this module and return its result object."""
    cached = _STATE.get("report")
    if isinstance(cached, dict):
        return cached
    queued = start_dedup_check(api, admin)
    finished = wait_for_job(api, admin, queued["job_id"])
    assert str(finished.get("status", "")).lower() in {
        "finished",
        "completed",
        "complete",
        "succeeded",
        "success",
    }, f"the de-duplication check did not succeed: {str(finished)[:300]}"
    result = finished.get("result")
    assert isinstance(result, dict), (
        f"the finished de-duplication check carries no result object: {str(finished)[:300]}"
    )
    _STATE["report"] = result
    return result
