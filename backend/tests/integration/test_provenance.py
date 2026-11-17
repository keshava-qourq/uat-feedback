"""US-002: provenance on every stored fact, proved against the real ingest API.

AC-005 every stored event carries its source fields; AC-006 `source_ref` works
as the join key back to the note or imaging report text in notes.csv; AC-007 a
row missing `source_type` or `source_ref` is reported as a provenance failure
in the ingest report and is not available to scoring or display.

Everything here goes through the real HTTP API against the sandbox's real
PostgreSQL and Redis: the bootstrap admin signs in through POST /api/auth/login
(the only sign-in), the cohort is created by POST /api/admin/ingest-runs over a
fixture drop written to the application's own storage, and every assertion
reads what an API route answers. No row is inserted by hand, and the fixture
drop is unique per test so concurrent runs never share a patient.
"""

from __future__ import annotations

import os
import uuid
from typing import Any

from fastapi.testclient import TestClient

from tests.integration import fixtures_dataset as fx
from tests.integration.conftest import admin_headers, start_ingest, wait_for_run
from tests.integration.fixtures_provenance import AC005_FIELDS, AC005_SIXTEENTH, ProvenanceDrop

#: What each AC-005 field may be called in a payload. `event_id` is the id the
#: source file gave the row, which the data model stores as `source_event_id`.
FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "patient_id": ("patient_id",),
    "event_id": ("event_id", "source_event_id"),
    "event_time": ("event_time", "item_time", "occurred_at"),
    "event_type": ("event_type",),
    "code_system": ("code_system",),
    "code": ("code",),
    "display": ("display",),
    "value": ("value",),
    "unit": ("unit",),
    "provider_org": ("provider_org",),
    "provider_specialty": ("provider_specialty",),
    "source_type": ("source_type",),
    "source_ref": ("source_ref",),
    "encounter_ref": ("encounter_ref",),
    "confidence": ("confidence",),
}


def _drain_ingest_queue() -> None:
    """Run whatever is on the ingest queue, as the deployed RQ worker would."""
    import redis
    from rq import Queue, SimpleWorker

    connection = redis.from_url(os.environ["REDIS_URL"])
    queue = Queue("ingest", connection=connection)
    SimpleWorker([queue], connection=connection).work(burst=True)


def _ingest(
    api: TestClient, headers: dict[str, str], drop: ProvenanceDrop
) -> tuple[dict[str, Any], str]:
    """Load `drop` through the real ingest API; return (report, dataset_version)."""
    files = drop.files()
    source_uri, _prefix = fx.upload_fixture_set(files)
    version = f"qa-prov-{drop.suffix}"
    _drain_ingest_queue()
    started = start_ingest(api, headers, dataset_version=version, source_uri=source_uri, seed=17)
    _drain_ingest_queue()
    return wait_for_run(api, headers, started["run_id"]), version


def _objects(payload: Any) -> list[dict]:
    """Every JSON object anywhere in a payload."""
    found: list[dict] = []
    if isinstance(payload, dict):
        found.append(payload)
        for value in payload.values():
            found.extend(_objects(value))
    elif isinstance(payload, list):
        for item in payload:
            found.extend(_objects(item))
    return found


def _strings(payload: Any) -> list[str]:
    if isinstance(payload, str):
        return [payload]
    if isinstance(payload, dict):
        out: list[str] = []
        for key, value in payload.items():
            out.append(str(key))
            out.extend(_strings(value))
        return out
    if isinstance(payload, list):
        out = []
        for item in payload:
            out.extend(_strings(item))
        return out
    return [] if payload is None else [str(payload)]


def _patient_uuids(
    api: TestClient, headers: dict[str, str], drop: ProvenanceDrop
) -> dict[str, str]:
    """dataset patient id -> internal uuid, read back through GET /api/worklist."""
    response = api.get("/api/worklist", headers=headers)
    assert response.status_code == 200, (
        f"GET /api/worklist returned {response.status_code}: {response.text[:200]}"
    )
    rows = _objects(response.json())
    wanted = set(drop.patient_ids)
    found = {
        str(row["dataset_patient_id"]): str(row["patient_id"])
        for row in rows
        if row.get("dataset_patient_id") in wanted and row.get("patient_id")
    }
    assert found, (
        "none of the patients just ingested are visible through the API: "
        f"{sorted(wanted)} not among the cohort"
    )
    return found


def _read_payloads(
    api: TestClient, headers: dict[str, str], drop: ProvenanceDrop
) -> dict[str, Any]:
    """Every read route that can show this drop's data, path -> payload.

    A route that this build does not answer with 200 is left out; what matters
    is that whatever *is* exposed carries provenance (AC-005) and never carries
    a provenance-failed row (AC-007).
    """
    payloads: dict[str, Any] = {}
    for path in ("/api/worklist", "/api/patients/me/timeline", "/api/patients/me/updates"):
        response = api.get(path, headers=headers)
        if response.status_code == 200:
            payloads[path] = response.json()

    for dataset_id, patient_uuid in _patient_uuids(api, headers, drop).items():
        for path in (
            f"/api/cases/{patient_uuid}/timeline",
            f"/api/cases/{patient_uuid}",
        ):
            response = api.get(path, headers=headers)
            if response.status_code == 200:
                payloads[f"{path} ({dataset_id})"] = response.json()

    persona_key = f"prov-ada-{drop.suffix}"
    opened = api.post(
        f"/api/demo/personas/{persona_key}/open", headers=headers, json={"view": "clinician"}
    )
    if opened.status_code == 200:
        payloads[f"POST /api/demo/personas/{persona_key}/open"] = opened.json()
    replay = api.get(f"/api/demo/personas/{persona_key}/replay", headers=headers)
    if replay.status_code == 200:
        payloads[f"/api/demo/personas/{persona_key}/replay"] = replay.json()
    return payloads


def _event_objects(payloads: dict[str, Any], drop: ProvenanceDrop) -> list[tuple[str, dict]]:
    """(route, object) for every payload object that is one of this drop's events."""
    event_ids = {event["event_id"] for event in drop.events}
    source_refs = {event["source_ref"] for event in drop.events if event["source_ref"]}
    found: list[tuple[str, dict]] = []
    for route, payload in payloads.items():
        for obj in _objects(payload):
            values = {str(v) for v in obj.values() if isinstance(v, str)}
            if values & event_ids or values & source_refs:
                found.append((route, obj))
    return found


def _missing_fields(obj: dict) -> list[str]:
    return [field for field, aliases in FIELD_ALIASES.items() if not any(a in obj for a in aliases)]


# ------------------------------------------------------------------------ AC-005


def test_ac005_every_stored_event_the_api_exposes_carries_all_sixteen_provenance_fields(
    api: TestClient,
) -> None:
    """AC-005: after ingesting events.csv, every stored event the API hands out
    carries patient_id, event_id, event_time, event_type, code_system, code,
    display, value, unit, provider_org, provider_specialty, source_type,
    source_ref, encounter_ref and confidence -- plus the load it came from."""
    headers = admin_headers(api)
    drop = ProvenanceDrop(uuid.uuid4().hex[:8])
    report, version = _ingest(api, headers, drop)
    assert str(report["run"]["status"]).lower() in {"succeeded", "success", "completed"}, (
        f"the fixture drop did not ingest cleanly: {report['run']}"
    )

    payloads = _read_payloads(api, headers, drop)
    events = _event_objects(payloads, drop)
    assert events, (
        "no route exposed any of the events just ingested, so provenance on a stored "
        f"event cannot be inspected; routes read: {sorted(payloads)}"
    )

    incomplete = [
        (route, obj.get("event_id") or obj.get("source_event_id"), _missing_fields(obj))
        for route, obj in events
        if _missing_fields(obj)
    ]
    assert not incomplete, (
        "these exposed events are missing AC-005 provenance fields (route, event, missing): "
        f"{incomplete}"
    )

    without_load = [
        route for route, obj in events if not any(field in obj for field in AC005_SIXTEENTH)
    ]
    assert not without_load, (
        "these exposed events name none of "
        f"{AC005_SIXTEENTH}, so the sixteenth provenance field -- which load the row "
        f"came from -- is absent: {without_load}"
    )

    by_source_event = {
        str(obj.get("event_id") or obj.get("source_event_id")): obj for _route, obj in events
    }
    original = {event["event_id"]: event for event in drop.good_events}
    for event_id, source_row in original.items():
        exposed = by_source_event.get(event_id)
        if exposed is None:
            continue
        for field in ("source_type", "source_ref", "code", "provider_org", "provider_specialty"):
            assert str(exposed.get(field)) == source_row[field], (
                f"event {event_id} was stored with {field}={exposed.get(field)!r}; "
                f"events.csv supplied {source_row[field]!r}"
            )
        if "dataset_version" in exposed:
            assert exposed["dataset_version"] == version

    assert len(AC005_FIELDS) == 15, "AC-005 names fifteen source fields plus the load"


# ------------------------------------------------------------------------ AC-006


def test_ac006_an_event_source_ref_resolves_to_the_matching_note_text(api: TestClient) -> None:
    """AC-006: an event whose source_type is ehr or patient and whose source_ref
    points at a note resolves, through the API, to that note's text in notes.csv
    -- source_ref is the provenance join key."""
    headers = admin_headers(api)
    drop = ProvenanceDrop(uuid.uuid4().hex[:8])
    report, _version = _ingest(api, headers, drop)
    assert str(report["run"]["status"]).lower() in {"succeeded", "success", "completed"}, (
        f"the fixture drop did not ingest cleanly: {report['run']}"
    )

    payloads = _read_payloads(api, headers, drop)
    unresolved: list[str] = []
    for source_ref, text in drop.note_texts.items():
        resolved = any(
            source_ref in _strings(obj) and text in _strings(obj)
            for payload in payloads.values()
            for obj in _objects(payload)
        )
        if not resolved:
            unresolved.append(source_ref)
    assert not unresolved, (
        "following these event source_refs did not retrieve the matching notes.csv "
        f"text through any read route: {unresolved}; routes read: {sorted(payloads)}"
    )


# ------------------------------------------------------------------------ AC-007


def test_ac007_rows_missing_source_ref_or_source_type_fail_provenance_and_are_not_retrievable(
    api: TestClient,
) -> None:
    """AC-007: an events.csv with one row missing source_ref and one missing
    source_type reports both as provenance failures in the ingest report, and
    neither row is retrievable from any read route."""
    headers = admin_headers(api)
    drop = ProvenanceDrop(uuid.uuid4().hex[:8], with_bad_rows=True)
    report, _version = _ingest(api, headers, drop)

    # The report names the provenance failures, per the ingest-report contract.
    failures = report.get("provenance_failures")
    assert failures is not None, (
        f"the ingest report carries no provenance_failures section: {sorted(report)}"
    )
    text = " ".join(_strings(failures))
    assert "source_ref" in text, (
        f"the row missing source_ref is not reported as a provenance failure: {text[:400]}"
    )
    assert "source_type" in text, (
        f"the row missing source_type is not reported as a provenance failure: {text[:400]}"
    )
    for event_id in (drop.missing_source_ref_event_id, drop.missing_source_type_event_id):
        assert event_id in text, (
            f"the provenance failures do not name the offending row {event_id}: {text[:400]}"
        )

    # events.csv itself still loaded its good rows, and counted the bad ones.
    files = {str(row.get("file_name", "")).split("/")[-1]: row for row in report.get("files") or []}
    events_file = files.get("events.csv")
    assert events_file is not None, f"the report has no line for events.csv: {sorted(files)}"
    assert events_file.get("rows_rejected", 0) >= 2, (
        f"the two provenance-failed rows were not counted as rejected: {events_file}"
    )
    assert events_file.get("rows_loaded", 0) == len(drop.good_events), (
        f"events.csv loaded {events_file.get('rows_loaded')} rows; the drop has "
        f"{len(drop.good_events)} well-formed rows and 2 provenance failures"
    )

    # And neither row reaches scoring or display: no read route shows it.
    payloads = _read_payloads(api, headers, drop)
    leaked: list[str] = []
    for route, payload in payloads.items():
        strings = set(_strings(payload))
        for marker in (
            drop.missing_source_ref_event_id,
            drop.missing_source_type_event_id,
            drop.missing_source_ref_display,
            drop.missing_source_type_display,
        ):
            if marker in strings:
                leaked.append(f"{route}: {marker}")
    assert not leaked, f"a provenance-failed row is retrievable through a read route: {leaked}"
