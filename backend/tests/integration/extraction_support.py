"""Shared helpers for the clue-extraction acceptance tests (US-015-4).

The cohort is built the way the behaviour rules and NFR-021 require: one
module-scoped ingest of an extraction fixture drop through the real API,
tolerating a 409 when another run is already in flight. Nothing is written into
the database by hand and no application module is imported to read data.

The extractor is run the way the contract says a screen runs it:
POST /api/admin/jobs {"kind": "extraction"} and then polling
GET /api/admin/jobs/{job_id} until it reaches a terminal status; the report is
read from GET /api/admin/extraction-report.
"""

from __future__ import annotations

import os
import time
import uuid
from typing import Any

from fastapi.testclient import TestClient

from tests.integration import fixtures_dataset as fx
from tests.integration.conftest import wait_for_run
from tests.integration.fixtures_extraction import (
    CLUE_TYPE_KEYS,
    NOTE_REF_KEYS,
    QUOTE_KEYS,
    ExtractionDrop,
)

INGEST_START = "/api/admin/ingest-runs"
JOBS = "/api/admin/jobs"
EXTRACTION_REPORT = "/api/admin/extraction-report"
WORKLIST = "/api/worklist"

TERMINAL = {"finished", "completed", "complete", "succeeded", "success", "failed", "error"}
SUCCEEDED = {"finished", "completed", "complete", "succeeded", "success"}


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


def text_of(obj: dict, keys: tuple[str, ...]) -> str:
    for key in keys:
        value = obj.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def findings(payload: Any) -> list[dict]:
    """Every object in `payload` that looks like an extracted clue finding:
    it carries a quoted sentence and a clue type."""
    return [
        obj for obj in objects(payload) if text_of(obj, QUOTE_KEYS) and text_of(obj, CLUE_TYPE_KEYS)
    ]


def quote_of(finding: dict) -> str:
    return text_of(finding, QUOTE_KEYS)


def clue_of(finding: dict) -> str:
    return text_of(finding, CLUE_TYPE_KEYS).lower()


def note_ref_of(finding: dict) -> str:
    """The finding's reference back to the note: its source_ref or a link to it."""
    direct = text_of(finding, NOTE_REF_KEYS)
    if direct:
        return direct
    for obj in objects(finding):
        found = text_of(obj, NOTE_REF_KEYS)
        if found:
            return found
    return ""


def drain_queues() -> None:
    """Run whatever is on any queue, as the deployed RQ worker would."""
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


def extraction_cohort(api: TestClient, admin: dict[str, str]) -> ExtractionDrop:
    """The extraction fixture cohort, ingested once per module through the real
    API. A 409 (NFR-021 serialises ingest) is tolerated once."""
    existing = _STATE.get("drop")
    if isinstance(existing, ExtractionDrop):
        return existing

    drop = ExtractionDrop(uuid.uuid4().hex[:8])
    source_uri, _prefix = fx.upload_fixture_set(drop.files())
    for attempt in range(2):
        drain_queues()
        response = api.post(
            INGEST_START,
            headers=admin,
            json={
                "dataset_version": drop.dataset_version,
                "source_uri": source_uri,
                "seed": 37,
            },
        )
        drain_queues()
        if response.status_code == 409 and attempt == 0:
            continue
        assert response.status_code in (200, 202), (
            f"starting the extraction cohort's ingest run returned "
            f"{response.status_code}: {response.text[:300]}"
        )
        wait_for_run(api, admin, response.json()["run_id"])
        break
    _STATE["drop"] = drop
    return drop


def patient_uuids(api: TestClient, admin: dict[str, str], drop: ExtractionDrop) -> dict[str, str]:
    """dataset patient id -> internal uuid for this drop, read from the worklist."""
    wanted = set(drop.patient_ids)
    found = {
        str(row["dataset_patient_id"]): str(row["patient_id"])
        for row in worklist_rows(api, admin)
        if row.get("dataset_patient_id") in wanted
    }
    assert set(found) == wanted, (
        f"these extraction fixture patients are not visible through GET {WORKLIST}, so "
        f"the extractor cannot be checked over their notes: {sorted(wanted - set(found))}"
    )
    return found


def start_extraction(api: TestClient, admin: dict[str, str]) -> dict:
    """POST /api/admin/jobs {"kind": "extraction"} -> 202 {job_id, kind, status}."""
    response = api.post(JOBS, headers=admin, json={"kind": "extraction"})
    assert response.status_code == 202, (
        f"POST {JOBS} {{'kind': 'extraction'}} returned {response.status_code}, not 202: "
        f"{response.text[:300]}"
    )
    body = response.json()
    assert body.get("job_id"), f"the queued extraction job carries no job_id: {str(body)[:300]}"
    assert body.get("kind") == "extraction", (
        f"the queued job reports kind {body.get('kind')!r}, not 'extraction'"
    )
    assert body.get("status"), f"the queued extraction job carries no status: {str(body)[:300]}"
    return body


def wait_for_job(
    api: TestClient, admin: dict[str, str], job_id: str, timeout: float = 180.0
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
        f"the extraction job {job_id} did not finish within {timeout:.0f}s; "
        f"last status: {str(body)[:300]}"
    )


def extraction_run(api: TestClient, admin: dict[str, str]) -> dict:
    """Run the extractor once for this module and return the finished job body."""
    cached = _STATE.get("job")
    if isinstance(cached, dict):
        return cached
    queued = start_extraction(api, admin)
    finished = wait_for_job(api, admin, queued["job_id"])
    assert str(finished.get("status", "")).lower() in SUCCEEDED, (
        f"the extraction job did not succeed: {str(finished)[:300]}"
    )
    _STATE["job"] = finished
    return finished


def extraction_report(api: TestClient, admin: dict[str, str]) -> dict:
    """GET /api/admin/extraction-report, after the extractor has been run."""
    extraction_run(api, admin)
    response = api.get(EXTRACTION_REPORT, headers=admin)
    assert response.status_code == 200, (
        f"GET {EXTRACTION_REPORT} returned {response.status_code}: {response.text[:300]}"
    )
    body = response.json()
    assert isinstance(body, dict), f"the extraction report is not an object: {str(body)[:300]}"
    return body


def case_payloads(api: TestClient, admin: dict[str, str], patient_uuid: str) -> dict[str, Any]:
    """Every read of a case that may carry an evidence item, route -> payload."""
    payloads: dict[str, Any] = {}
    for path in (
        f"/api/cases/{patient_uuid}",
        f"/api/cases/{patient_uuid}/evidence",
        f"/api/cases/{patient_uuid}/timeline",
    ):
        response = api.get(path, headers=admin)
        if response.status_code == 200:
            payloads[path] = response.json()
    return payloads
