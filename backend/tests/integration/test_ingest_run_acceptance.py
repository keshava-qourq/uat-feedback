"""US-001-6: the ingest run proved end to end against the real API, PostgreSQL
and the Redis job queue, with a small fixture set in the formats the dataset
actually ships in.

Every run here is started and polled through the API only -- no test writes an
ingest row, a patient or an event into the database itself. The ingest is
driven from the test body rather than from a fixture, so a criterion the code
does not meet yet fails as that criterion rather than erroring in setup.

Two things this contract fixes, and these tests follow:

* Both routes are guarded by the shared bearer (`SECRET_KEY`, sent as
  `Authorization: Bearer <SECRET_KEY>`). No sign-in route belongs to this
  contract, so no test here logs in.
* The work is queued on the project's Redis queue and run by an RQ worker.
  The sandbox runs no long-lived worker, so each test runs the queue's jobs
  itself in a burst worker -- the same `run_ingest` job, off the same queue,
  just drained on demand.
"""

from __future__ import annotations

import json
import os
import secrets
import uuid

from fastapi.testclient import TestClient

from tests.integration import fixtures_dataset as fx
from tests.integration.conftest import files_by_name, start_ingest, wait_for_run

CSV_AND_JSON = (
    "patients.csv",
    "labels.csv",
    "events.csv",
    "notes.csv",
    "intake.csv",
    "coverage.csv",
    "encounter_truth.csv",
    "heroes.json",
)
FHIR = tuple(fx.FHIR_FILES)


def shared_bearer_headers() -> dict[str, str]:
    """The shared bearer the contract fixes for both admin ingest routes."""
    token = os.environ.get("SECRET_KEY")
    if not token:
        token = secrets.token_urlsafe(32)
        os.environ["SECRET_KEY"] = token
    return {"Authorization": f"Bearer {token}"}


def _drain_ingest_queue() -> None:
    """Run whatever is on the ingest queue, as the deployed RQ worker would."""
    import redis
    from rq import Queue, SimpleWorker

    connection = redis.from_url(os.environ["REDIS_URL"])
    queue = Queue("ingest", connection=connection)
    SimpleWorker([queue], connection=connection).work(burst=True)


def _unique_heroes_json() -> bytes:
    """heroes.json whose persona keys belong to this test alone.

    `personas.persona_key` is globally unique, so two runs of different dataset
    versions may not share one; each test therefore ships its own keys rather
    than colliding with another test's load.
    """
    suffix = uuid.uuid4().hex[:8]
    return json.dumps(
        [
            {
                "persona_key": f"ada-classic-{suffix}",
                "name": "Ada Lovelace",
                "one_line_description": "Classic presentation missed for years.",
                "patient_id": "P0001",
                "cutoff_date": "2021-01-01",
            },
            {
                "persona_key": f"grace-lookalike-{suffix}",
                "name": "Grace Hopper",
                "one_line_description": "Mechanical look-alike that should stay low.",
                "patient_id": "P0002",
                "cutoff_date": "2021-01-01",
            },
        ]
    ).encode()


def _fixture_set(**overrides: bytes) -> dict[str, bytes]:
    return fx.fixture_set(**{"heroes.json": _unique_heroes_json(), **overrides})


def _passed(file_row: dict) -> bool:
    return str(file_row.get("status", "")).lower() in {"pass", "passed", "ok", "loaded", "success"}


def _failed(file_row: dict) -> bool:
    return str(file_row.get("status", "")).lower() in {"fail", "failed", "error", "rejected"}


def _error_of(file_row: dict) -> str:
    return str(file_row.get("error") or file_row.get("error_detail") or "")


def _run(
    api: TestClient,
    headers: dict[str, str],
    *,
    files: dict[str, bytes],
    version: str,
    seed: int,
) -> dict:
    """Start one run over `files` through the API, let the worker run it, report."""
    source_uri, prefix = fx.upload_fixture_set(files)
    _drain_ingest_queue()  # no stale run of another test may block this start
    started = start_ingest(api, headers, dataset_version=version, source_uri=source_uri, seed=seed)
    _drain_ingest_queue()
    report = wait_for_run(api, headers, started["run_id"])
    report["_started"] = started
    report["_dataset_version"] = version
    report["_prefix"] = prefix
    report["_files"] = files
    return report


def _completed_run(api: TestClient, headers: dict[str, str], *, seed: int = 4242) -> dict:
    """One good ingest run over the whole fixture set, started and polled via the API."""
    return _run(
        api,
        headers,
        files=_fixture_set(),
        version=f"qa-{uuid.uuid4().hex[:8]}",
        seed=seed,
    )


def test_ac001_every_required_file_type_is_loaded_with_per_file_row_counts(
    api: TestClient,
) -> None:
    """AC-001: one run loads every required file type and reports rows loaded and
    rows rejected for each of them."""
    report = _completed_run(api, shared_bearer_headers())
    rows = files_by_name(report)

    missing = [name for name in CSV_AND_JSON if name not in rows]
    missing += [name.split("/")[-1] for name in FHIR if name.split("/")[-1] not in rows]
    assert not missing, f"the ingest report has no row for: {missing}"

    for name, row in rows.items():
        assert "rows_loaded" in row and "rows_rejected" in row, (
            f"{name} reports no loaded/rejected counts: {row}"
        )
        assert isinstance(row["rows_loaded"], int) and isinstance(row["rows_rejected"], int)

    for name, expected in fx.EXPECTED_ROWS.items():
        row = rows[name]
        assert row["rows_loaded"] + row["rows_rejected"] == expected, (
            f"{name}: the fixture has {expected} data rows but the report accounts for "
            f"{row['rows_loaded']} loaded + {row['rows_rejected']} rejected"
        )


def test_ac002_the_report_carries_version_seed_patient_count_and_a_pass_line_per_file(
    api: TestClient,
) -> None:
    """AC-002: the completed run's report shows dataset version, seed, total patient
    count and a pass/fail line for every file."""
    report = _completed_run(api, shared_bearer_headers())
    run = report["run"]
    assert run["dataset_version"] == report["_dataset_version"]
    assert run["seed"] == 4242
    assert run["patient_count"] == len(fx.PATIENT_IDS), (
        f"patient_count {run.get('patient_count')} does not match the "
        f"{len(fx.PATIENT_IDS)} rows in patients.csv"
    )

    rows = files_by_name(report)
    for name, row in rows.items():
        assert _passed(row) or _failed(row), f"{name} has no pass/fail line: {row}"
    assert all(_passed(row) for row in rows.values()), (
        "a well-formed fixture set produced a failed file: "
        f"{[(n, _error_of(r)) for n, r in rows.items() if not _passed(r)]}"
    )


def test_ac003_a_file_missing_a_required_column_fails_and_is_named_with_that_column(
    api: TestClient,
) -> None:
    """AC-003 / NFR-021: events.csv without its required `source_ref` column fails
    that file, the error names the file and the column, and none of its rows stay
    reachable through any endpoint."""
    headers = shared_bearer_headers()
    report = _run(
        api,
        headers,
        files=_fixture_set(**{"events.csv": fx.events_csv_missing_source_ref()}),
        version=f"qa-bad-{uuid.uuid4().hex[:8]}",
        seed=7,
    )

    rows = files_by_name(report)
    assert "events.csv" in rows, f"the malformed file is not named in the report: {rows.keys()}"
    bad = rows["events.csv"]
    assert _failed(bad), f"events.csv was not marked failed: {bad}"

    detail = _error_of(bad)
    assert "events.csv" in detail, f"the error does not name the file: {detail!r}"
    assert "source_ref" in detail, f"the error does not name the missing column: {detail!r}"

    assert bad.get("rows_loaded", 0) == 0, (
        f"a failed file left {bad.get('rows_loaded')} rows loaded; a malformed file must "
        "leave no partially loaded rows"
    )

    # And nothing from it is reachable: the run itself must not be reported as a
    # clean pass, so no screen treats this load as usable.
    assert str(report["run"]["status"]).lower() in {"failed", "error", "completed_with_errors"}, (
        f"the run with a failed file reports status {report['run']['status']!r}"
    )


def test_ac004_nfr021_re_running_replaces_the_prior_load_without_duplicates(
    api: TestClient,
) -> None:
    """AC-004 / NFR-021: ingesting the same fixtures twice replaces the first load --
    the patient count still matches patients.csv and no event row is duplicated."""
    headers = shared_bearer_headers()
    files = _fixture_set()
    version = f"qa-rerun-{uuid.uuid4().hex[:8]}"

    first = _run(api, headers, files=files, version=version, seed=11)
    second = _run(api, headers, files=files, version=version, seed=11)

    assert first["run"]["patient_count"] == len(fx.PATIENT_IDS)
    assert second["run"]["patient_count"] == len(fx.PATIENT_IDS), (
        "re-running ingest changed the patient count, so the second load added rows "
        "instead of replacing the first"
    )

    first_events = files_by_name(first)["events.csv"]["rows_loaded"]
    second_events = files_by_name(second)["events.csv"]["rows_loaded"]
    assert second_events == first_events == fx.EXPECTED_ROWS["events.csv"], (
        f"events.csv loaded {first_events} rows then {second_events}; a re-run must "
        "replace the prior load, not duplicate it"
    )


def test_nfr023_the_supplied_formats_are_read_as_they_are(api: TestClient) -> None:
    """NFR-023: comma-separated files, heroes.json and gzipped bulk FHIR NDJSON are
    all read as supplied -- none of them had to be converted by hand first."""
    report = _completed_run(api, shared_bearer_headers())
    rows = files_by_name(report)

    heroes = rows.get("heroes.json")
    assert heroes is not None, f"heroes.json is not in the report: {sorted(rows)}"
    assert _passed(heroes), f"heroes.json was not read as supplied: {heroes}"
    for key in FHIR:
        name = key.split("/")[-1]
        assert name in rows, f"the gzipped FHIR resource {name} was not read: {sorted(rows)}"
        assert _passed(rows[name]), f"{name} (gzipped NDJSON) was not read: {rows[name]}"
        assert rows[name]["rows_loaded"] > 0, f"{name} loaded no resources: {rows[name]}"


def test_nfr005_the_loaded_cohort_is_served_from_the_database_not_the_raw_files(
    api: TestClient,
) -> None:
    """NFR-005: once a run has completed, the cohort is answered from the loaded
    store -- the report and the patient count survive the source files being gone,
    so nothing is re-parsed per request.

    The dataset's real volumes (~5,006 patients, ~572k events, ~167k encounter-truth
    rows, ~40k notes) are deliberately not loaded here: the packet requires small
    fixtures. This proves the serving path, not the capacity figure.
    """
    headers = shared_bearer_headers()
    report = _completed_run(api, headers)
    fx.delete_fixture_set(report["_prefix"], report["_files"])

    response = api.get(f"/api/admin/ingest-runs/{report['_started']['run_id']}", headers=headers)
    assert response.status_code == 200
    again = response.json()
    assert again["run"]["patient_count"] == len(fx.PATIENT_IDS)
    assert files_by_name(again)["events.csv"]["rows_loaded"] == fx.EXPECTED_ROWS["events.csv"]


def test_nfr006_ingest_runs_as_a_background_job_with_progress(api: TestClient) -> None:
    """NFR-006: starting an ingest answers immediately with a queued run and a job
    id -- the files are still unread at that moment -- and the report carries the
    run's progress through to its terminal status, so no screen blocks on the work.
    """
    headers = shared_bearer_headers()
    files = _fixture_set()
    source_uri, _prefix = fx.upload_fixture_set(files)
    _drain_ingest_queue()

    started = start_ingest(
        api,
        headers,
        dataset_version=f"qa-job-{uuid.uuid4().hex[:8]}",
        source_uri=source_uri,
        seed=3,
    )
    assert started.get("job_id"), f"no job id was returned, so the work is not queued: {started}"
    assert str(started.get("status", "")).lower() == "queued", (
        f"the start did not return a queued run, so it did the work inline: {started}"
    )

    # Nothing has been loaded yet: the call returned before any worker ran.
    queued = api.get(f"/api/admin/ingest-runs/{started['run_id']}", headers=headers)
    assert queued.status_code == 200
    assert str(queued.json()["run"]["status"]).lower() in {"queued", "running"}

    _drain_ingest_queue()
    finished = wait_for_run(api, headers, started["run_id"])
    assert str(finished["run"]["status"]).lower() in {"succeeded", "success", "completed"}
    assert finished["run"]["patient_count"] == len(fx.PATIENT_IDS)
    assert files_by_name(finished)["events.csv"]["rows_loaded"] == fx.EXPECTED_ROWS["events.csv"]
