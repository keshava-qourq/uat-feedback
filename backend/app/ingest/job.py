"""The dataset ingest background job (RQ).

Streams the eight files of a dataset drop -- patients.csv, labels.csv,
events.csv, notes.csv, intake.csv, coverage.csv, encounter_truth.csv and
heroes.json -- into the event store, in that order (every other file is
patient-scoped, so patients.csv has to land first).

Three rules shape the design:

* **Streaming.** Every comma-separated file is read with pandas in chunks and
  inserted chunk by chunk, so a 572k-row events.csv is never held in memory
  (NFR-005). The heroes file is the one exception: it is a handful of personas.
* **One transaction per file.** A file loads inside a transaction of its own and
  commits only when the whole file has been read. A missing required column or
  any other failure rolls that file back, so no partial rows are ever queryable
  (NFR-021), and the file's `error_detail` names the file and the column.
* **Replace, never duplicate.** Re-running against the same `dataset_version`
  first deletes the prior load for that version, so the job is safe to run
  twice and the patient count still matches patients.csv (NFR-021).

Progress -- the file being worked on and the rows processed so far -- is
written to `ingest_file_results` from a second, short-lived session as the job
proceeds, so a polling screen sees it while the file's own transaction is still
open (NFR-006).
"""

from __future__ import annotations

import gzip
import json
import math
import os
import uuid
from collections.abc import Callable, Iterator
from datetime import UTC, datetime
from typing import Any, BinaryIO

import pandas as pd
from sqlalchemy import delete, insert, select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.ingest.source import list_source_files, open_source_file
from app.models import (
    CoveragePeriod,
    Decision,
    EncounterTruth,
    Event,
    IngestFileResult,
    IngestRun,
    IntakeAnswer,
    Invite,
    Note,
    Patient,
    Persona,
)

CHUNK_SIZE = 5_000

#: The files this job loads, in the order it loads them.
DATASET_FILES: tuple[str, ...] = (
    "patients.csv",
    "labels.csv",
    "events.csv",
    "notes.csv",
    "intake.csv",
    "coverage.csv",
    "encounter_truth.csv",
    "heroes.json",
)

REQUIRED_COLUMNS: dict[str, tuple[str, ...]] = {
    "patients.csv": ("patient_id", "display_name"),
    "labels.csv": ("patient_id", "split"),
    "events.csv": (
        "patient_id",
        "event_id",
        "event_type",
        "source_type",
        "source_ref",
    ),
    "notes.csv": ("patient_id", "source_ref", "note_type", "text"),
    "intake.csv": ("patient_id", "question_key", "answer_value", "answered_at"),
    "coverage.csv": ("patient_id",),
    "encounter_truth.csv": ("patient_id", "true_encounter_id", "encounter_time"),
    "heroes.json": ("persona_key", "name", "patient_id"),
}


class MissingColumnError(Exception):
    """A required column is not in the file at all: the whole file fails."""

    def __init__(self, file_name: str, column: str) -> None:
        super().__init__(f"{file_name}: required column '{column}' is missing")
        self.file_name = file_name
        self.column = column


class _Rejected(Exception):
    """One row could not be loaded. Counted, not inserted."""


class _ProvenanceFailure(_Rejected):
    """A row with no usable provenance: never inserted, counted and named (AC-007).

    Provenance is `source_type` (one of ehr|claim|patient) and `source_ref`;
    without both, an event could never be traced back to where it came from,
    so it may not reach scoring or a screen at all.
    """


#: How many provenance failures one file's `error_detail` names before it stops
#: listing them: enough to see what is wrong, bounded so a broken drop cannot
#: write a megabyte of text into the report.
MAX_REPORTED_FAILURES = 20

#: The only source types a stored event may carry (AC-005).
SOURCE_TYPES: frozenset[str] = frozenset({"ehr", "claim", "patient"})


# --------------------------------------------------------------------------- values


def _text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    text = str(value).strip()
    return text or None


def _required_text(value: Any, column: str) -> str:
    text = _text(value)
    if text is None:
        raise _Rejected(f"'{column}' is empty")
    return text


def _timestamp(value: Any, column: str, *, required: bool = False) -> datetime | None:
    text = _text(value)
    if text is None:
        if required:
            raise _Rejected(f"'{column}' is empty")
        return None
    parsed = pd.to_datetime(text, utc=True, errors="coerce")
    if parsed is pd.NaT or pd.isna(parsed):
        raise _Rejected(f"'{column}' is not a timestamp")
    return parsed.to_pydatetime()


def _date(value: Any, column: str):
    stamp = _timestamp(value, column)
    return None if stamp is None else stamp.date()


def _number(value: Any, column: str) -> float | None:
    text = _text(value)
    if text is None:
        return None
    try:
        return float(text)
    except ValueError as exc:
        raise _Rejected(f"'{column}' is not a number") from exc


def _integer(value: Any, column: str) -> int | None:
    number = _number(value, column)
    return None if number is None else int(number)


def _boolean(value: Any) -> bool:
    return _text(value) is not None and str(value).strip().lower() in {
        "true",
        "t",
        "1",
        "yes",
        "y",
    }


def _json_value(value: Any) -> Any:
    text = _text(value)
    if text is None:
        return None
    try:
        return json.loads(text)
    except ValueError:
        return text


# --------------------------------------------------------------------------- rows


def _patient_row(row: dict, version: str, _ids: dict[str, str]) -> dict:
    return {
        "id": str(uuid.uuid4()),
        "dataset_patient_id": _required_text(row.get("patient_id"), "patient_id"),
        "dataset_version": version,
        "display_name": _required_text(row.get("display_name"), "display_name"),
        "birth_year": _integer(row.get("birth_year"), "birth_year"),
        "sex": _text(row.get("sex")),
        "reachable_history_start": _date(
            row.get("reachable_history_start"), "reachable_history_start"
        ),
    }


def _patient_id(row: dict, ids: dict[str, str]) -> str:
    dataset_id = _required_text(row.get("patient_id"), "patient_id")
    internal = ids.get(dataset_id)
    if internal is None:
        raise _Rejected(f"patient '{dataset_id}' is not in patients.csv")
    return internal


def _provenance(row: dict, event_id: str) -> tuple[str, str]:
    """`(source_type, source_ref)`, or a provenance failure naming what is missing."""
    source_type = _text(row.get("source_type"))
    source_ref = _text(row.get("source_ref"))
    if source_type is None:
        raise _ProvenanceFailure(f"event '{event_id}' is missing source_type")
    if source_ref is None:
        raise _ProvenanceFailure(f"event '{event_id}' is missing source_ref")
    if source_type not in SOURCE_TYPES:
        raise _ProvenanceFailure(
            f"event '{event_id}' has source_type '{source_type}', "
            f"not one of {'|'.join(sorted(SOURCE_TYPES))}"
        )
    return source_type, source_ref


def _event_row(row: dict, version: str, ids: dict[str, str]) -> dict:
    event_id = _required_text(row.get("event_id"), "event_id")
    source_type, source_ref = _provenance(row, event_id)
    return {
        "id": str(uuid.uuid4()),
        "patient_id": _patient_id(row, ids),
        "source_event_id": event_id,
        "event_time": _timestamp(row.get("event_time"), "event_time"),
        "event_type": _required_text(row.get("event_type"), "event_type"),
        "code_system": _text(row.get("code_system")),
        "code": _text(row.get("code")),
        "display": _text(row.get("display")),
        "value": _text(row.get("value")),
        "unit": _text(row.get("unit")),
        "provider_org": _text(row.get("provider_org")),
        "provider_specialty": _text(row.get("provider_specialty")),
        "source_type": source_type,
        "source_ref": source_ref,
        "encounter_ref": _text(row.get("encounter_ref")),
        "confidence": _number(row.get("confidence"), "confidence"),
        "dataset_version": version,
    }


def _note_row(row: dict, _version: str, ids: dict[str, str]) -> dict:
    return {
        "id": str(uuid.uuid4()),
        "patient_id": _patient_id(row, ids),
        "source_ref": _required_text(row.get("source_ref"), "source_ref"),
        "note_time": _timestamp(row.get("note_time"), "note_time"),
        "note_type": _required_text(row.get("note_type"), "note_type"),
        "text": _required_text(row.get("text"), "text"),
    }


def _intake_row(row: dict, _version: str, ids: dict[str, str]) -> dict:
    return {
        "id": str(uuid.uuid4()),
        "patient_id": _patient_id(row, ids),
        "question_key": _required_text(row.get("question_key"), "question_key"),
        "answer_value": _json_value(row.get("answer_value")),
        "answered_at": _timestamp(row.get("answered_at"), "answered_at", required=True),
        "is_complete": _boolean(row.get("is_complete")),
    }


def _coverage_row(row: dict, _version: str, ids: dict[str, str]) -> dict:
    return {
        "id": str(uuid.uuid4()),
        "patient_id": _patient_id(row, ids),
        "payer": _text(row.get("payer")),
        "start_date": _date(row.get("start_date"), "start_date"),
        "end_date": _date(row.get("end_date"), "end_date"),
        "gap_reason": _text(row.get("gap_reason")),
    }


def _encounter_truth_row(row: dict, _version: str, ids: dict[str, str]) -> dict:
    return {
        "id": str(uuid.uuid4()),
        "patient_id": _patient_id(row, ids),
        "true_encounter_id": _required_text(row.get("true_encounter_id"), "true_encounter_id"),
        "encounter_time": _timestamp(row.get("encounter_time"), "encounter_time", required=True),
        "visible_in_sources": _boolean(row.get("visible_in_sources")),
        "matched_encounter_id": _text(row.get("matched_encounter_id")),
    }


def _persona_row(row: dict, _version: str, ids: dict[str, str]) -> dict:
    return {
        "id": str(uuid.uuid4()),
        "persona_key": _required_text(row.get("persona_key"), "persona_key"),
        "name": _required_text(row.get("name"), "name"),
        "one_line_description": _text(row.get("one_line_description")) or "",
        "patient_id": _patient_id(row, ids),
        "expected_outcome": row.get("expected_outcome"),
    }


def _label_row(row: dict, _version: str, ids: dict[str, str]) -> None:
    """labels.csv has no table of its own yet: its rows are validated and counted.

    The split/archetype/cutoff columns belong to the case and evaluation
    tickets; validating them here still means a malformed labels.csv fails the
    run rather than being discovered much later.
    """
    _patient_id(row, ids)
    _required_text(row.get("split"), "split")
    return None


# ----------------------------------------------------------------- bulk FHIR rows

#: resource type -> (the field naming its patient, the source_type of its events)
FHIR_RESOURCES: dict[str, tuple[str | None, str]] = {
    "Patient": (None, "ehr"),
    "Encounter": ("subject", "ehr"),
    "Condition": ("subject", "ehr"),
    "Observation": ("subject", "ehr"),
    "MedicationRequest": ("subject", "ehr"),
    "Claim": ("patient", "claim"),
}

FHIR_PREFIX = "fhir/"

_TIME_FIELDS = (
    "effectiveDateTime",
    "recordedDate",
    "onsetDateTime",
    "authoredOn",
    "occurrenceDateTime",
    "created",
)


def _reference_id(resource: dict, field: str) -> str:
    """The dataset patient id behind e.g. {"reference": "Patient/P0001"}."""
    value = resource.get(field)
    reference = value.get("reference") if isinstance(value, dict) else value
    text = _text(reference)
    if text is None:
        raise _Rejected(f"'{field}' is missing")
    return text.rsplit("/", 1)[-1]


def _fhir_time(resource: dict) -> datetime | None:
    for field in _TIME_FIELDS:
        if _text(resource.get(field)) is not None:
            return _timestamp(resource.get(field), field)
    for field in ("period", "billablePeriod"):
        block = resource.get(field)
        if isinstance(block, dict) and _text(block.get("start")) is not None:
            return _timestamp(block.get("start"), field)
    return None


def _fhir_coding(resource: dict) -> dict[str, str | None]:
    for field in ("code", "medicationCodeableConcept", "type"):
        block = resource.get(field)
        if isinstance(block, list):
            block = block[0] if block else None
        if isinstance(block, dict):
            codings = block.get("coding") or []
            if codings:
                coding = codings[0]
                return {
                    "code_system": _text(coding.get("system")),
                    "code": _text(coding.get("code")),
                    "display": _text(coding.get("display")) or _text(block.get("text")),
                }
    return {"code_system": None, "code": None, "display": None}


def _fhir_builder(
    resource_type: str,
) -> Callable[[dict, str, dict[str, str]], dict | None]:
    subject_field, source_type = FHIR_RESOURCES[resource_type]

    def build(row: dict, version: str, ids: dict[str, str]) -> dict | None:
        resource_id = _required_text(row.get("id"), "id")
        if subject_field is None:
            # A Patient resource adds no event; it is checked against the
            # cohort patients.csv loaded, and counted.
            if resource_id not in ids:
                raise _Rejected(f"patient '{resource_id}' is not in patients.csv")
            return None
        dataset_patient_id = _reference_id(row, subject_field)
        internal = ids.get(dataset_patient_id)
        if internal is None:
            raise _Rejected(f"patient '{dataset_patient_id}' is not in patients.csv")
        quantity = row.get("valueQuantity") if isinstance(row.get("valueQuantity"), dict) else {}
        encounter = row.get("encounter")
        return {
            "id": str(uuid.uuid4()),
            "patient_id": internal,
            "source_event_id": resource_id,
            "event_time": _fhir_time(row),
            "event_type": resource_type.lower(),
            **_fhir_coding(row),
            "value": _text(quantity.get("value")),
            "unit": _text(quantity.get("unit")),
            "provider_org": None,
            "provider_specialty": None,
            "source_type": source_type,
            "source_ref": f"fhir:{resource_type}:{resource_id}",
            "encounter_ref": (
                _text(encounter.get("reference")) if isinstance(encounter, dict) else None
            ),
            "confidence": None,
            "dataset_version": version,
        }

    return build


def _fhir_file_name(resource_type: str) -> str:
    return f"{FHIR_PREFIX}{resource_type}.ndjson.gz"


def _fhir_resource_type(file_name: str) -> str | None:
    if not file_name.startswith(FHIR_PREFIX) or not file_name.endswith(".ndjson.gz"):
        return None
    stem = file_name[len(FHIR_PREFIX) : -len(".ndjson.gz")]
    return stem if stem in FHIR_RESOURCES else None


def fhir_files_present(source_uri: str) -> list[str]:
    """The `fhir/<Type>.ndjson.gz` files this drop actually contains, in load order."""
    try:
        present = set(list_source_files(source_uri, FHIR_PREFIX))
    except Exception:  # noqa: BLE001 -- an unreadable prefix simply has no FHIR files
        return []
    return [
        _fhir_file_name(resource_type)
        for resource_type in FHIR_RESOURCES
        if _fhir_file_name(resource_type) in present
    ]


#: file -> (model or None, row builder)
_LOADERS: dict[str, tuple[Any, Callable[[dict, str, dict[str, str]], dict | None]]] = {
    "patients.csv": (Patient, _patient_row),
    "labels.csv": (None, _label_row),
    "events.csv": (Event, _event_row),
    "notes.csv": (Note, _note_row),
    "intake.csv": (IntakeAnswer, _intake_row),
    "coverage.csv": (CoveragePeriod, _coverage_row),
    "encounter_truth.csv": (EncounterTruth, _encounter_truth_row),
    "heroes.json": (Persona, _persona_row),
}


# --------------------------------------------------------------------------- reading


def _csv_chunks(stream: BinaryIO, file_name: str) -> Iterator[list[dict]]:
    required = REQUIRED_COLUMNS[file_name]
    seen_header = False
    for frame in pd.read_csv(stream, chunksize=CHUNK_SIZE, dtype=str, keep_default_na=False):
        if not seen_header:
            for column in required:
                if column not in frame.columns:
                    raise MissingColumnError(file_name, column)
            seen_header = True
        yield frame.to_dict("records")


def _json_chunks(stream: BinaryIO, file_name: str) -> Iterator[list[dict]]:
    payload = json.loads(stream.read().decode("utf-8"))
    records = payload if isinstance(payload, list) else payload.get("personas", [])
    for index in range(0, len(records), CHUNK_SIZE):
        chunk = records[index : index + CHUNK_SIZE]
        for column in REQUIRED_COLUMNS[file_name]:
            if any(column not in record for record in chunk):
                raise MissingColumnError(file_name, column)
        yield chunk


def _ndjson_gz_chunks(stream: BinaryIO, file_name: str) -> Iterator[list[dict]]:
    """Stream-decompress a gzipped NDJSON file line by line, never whole.

    `gzip.GzipFile` wraps the raw byte stream, so only one decompressed line at
    a time is held, however large the file is (NFR-005).
    """
    chunk: list[dict] = []
    with gzip.GzipFile(fileobj=stream, mode="rb") as unzipped:
        for line in unzipped:
            text = line.decode("utf-8").strip()
            if not text:
                continue
            try:
                record = json.loads(text)
            except ValueError as exc:
                raise MissingColumnError(file_name, f"valid JSON ({exc})") from exc
            if not isinstance(record, dict):
                raise MissingColumnError(file_name, "a JSON object per line")
            chunk.append(record)
            if len(chunk) >= CHUNK_SIZE:
                yield chunk
                chunk = []
    if chunk:
        yield chunk


def _chunks(stream: BinaryIO, file_name: str) -> Iterator[list[dict]]:
    if file_name.endswith(".ndjson.gz"):
        return _ndjson_gz_chunks(stream, file_name)
    if file_name.endswith(".json"):
        return _json_chunks(stream, file_name)
    return _csv_chunks(stream, file_name)


# --------------------------------------------------------------------------- progress


def _progress(run_id: str, file_name: str, **values: Any) -> None:
    """Write this file's current state in its own committed transaction."""
    session = SessionLocal()
    try:
        result = (
            session.execute(
                select(IngestFileResult).where(
                    IngestFileResult.ingest_run_id == run_id,
                    IngestFileResult.file_name == file_name,
                )
            )
            .scalars()
            .first()
        )
        if result is None:
            result = IngestFileResult(ingest_run_id=run_id, file_name=file_name, status="running")
            session.add(result)
        for key, value in values.items():
            setattr(result, key, value)
        session.commit()
    finally:
        session.close()


def _run_state(run_id: str, **values: Any) -> None:
    session = SessionLocal()
    try:
        run = session.get(IngestRun, run_id)
        if run is not None:
            for key, value in values.items():
                setattr(run, key, value)
            session.commit()
    finally:
        session.close()


# --------------------------------------------------------------------------- replace


def _purge(db: Session, dataset_version: str) -> None:
    """Remove the prior load of this dataset version, children first.

    Every table that carries a foreign key to `patients` has to be listed here:
    one that is not makes the delete of the patient row a foreign-key violation,
    which fails the whole job and leaves its run stuck in `running`.
    """
    patient_ids = select(Patient.id).where(Patient.dataset_version == dataset_version)
    for model in (
        Persona,
        IntakeAnswer,
        Note,
        CoveragePeriod,
        EncounterTruth,
        Event,
        Invite,
        Decision,
    ):
        db.execute(delete(model).where(model.patient_id.in_(patient_ids)))
    db.execute(delete(Patient).where(Patient.dataset_version == dataset_version))


# --------------------------------------------------------------------------- the job


def _load_file(
    run_id: str,
    file_name: str,
    *,
    source_uri: str,
    dataset_version: str,
    ids: dict[str, str],
) -> dict[str, Any]:
    """Load one file inside one transaction; return its per-file result values."""
    resource_type = _fhir_resource_type(file_name)
    if resource_type is not None:
        model, build = Event, _fhir_builder(resource_type)
    else:
        model, build = _LOADERS[file_name]
    loaded = 0
    rejected = 0
    provenance_failures = 0
    first_rejection: str | None = None
    provenance_messages: list[str] = []
    _progress(
        run_id,
        file_name,
        status="running",
        rows_loaded=0,
        rows_rejected=0,
        provenance_failures=0,
    )

    db = SessionLocal()
    try:
        with open_source_file(source_uri, file_name) as stream:
            for chunk in _chunks(stream, file_name):
                mappings: list[dict] = []
                for row in chunk:
                    try:
                        built = build(row, dataset_version, ids)
                    except _ProvenanceFailure as exc:
                        rejected += 1
                        provenance_failures += 1
                        if len(provenance_messages) < MAX_REPORTED_FAILURES:
                            provenance_messages.append(f"{file_name}: provenance failure: {exc}")
                        continue
                    except _Rejected as exc:
                        rejected += 1
                        if first_rejection is None:
                            first_rejection = f"{file_name}: {exc}"
                        continue
                    if built is not None:
                        mappings.append(built)
                    loaded += 1
                if mappings and model is not None:
                    db.execute(insert(model), mappings)
                    if model is Patient:
                        for mapping in mappings:
                            ids[mapping["dataset_patient_id"]] = mapping["id"]
                _progress(
                    run_id,
                    file_name,
                    rows_loaded=loaded,
                    rows_rejected=rejected,
                    provenance_failures=provenance_failures,
                )
        db.commit()
    except BaseException:
        db.rollback()
        if model is Patient:
            ids.clear()
        raise
    finally:
        db.close()

    return {
        "status": "pass",
        "rows_loaded": loaded,
        "rows_rejected": rejected,
        "provenance_failures": provenance_failures,
        # A provenance failure is reported first, and every one of them is
        # named: an unsourced event is the loudest thing a drop can be wrong
        # about (AC-007).
        "error_detail": "; ".join(provenance_messages) or first_rejection,
    }


def run_ingest(
    run_id: str, dataset_version: str, source_uri: str, seed: int | None = None
) -> dict[str, Any]:
    """Load a whole dataset drop. Safe to run twice: the prior load is replaced."""
    _run_state(run_id, status="running", seed=seed, dataset_version=dataset_version)

    # Replacing the prior load is its own transaction: once it commits, nothing
    # of the previous run is queryable, duplicates included (NFR-021).
    db = SessionLocal()
    try:
        _purge(db, dataset_version)
        db.commit()
    except Exception as exc:  # noqa: BLE001 -- a run that cannot start must not stay "running"
        db.rollback()
        _run_state(run_id, status="failed", finished_at=datetime.now(UTC))
        return {"run_id": run_id, "status": "failed", "patient_count": 0, "error": str(exc)}
    finally:
        db.close()

    ids: dict[str, str] = {}
    failed = False
    patient_count = 0
    # The bulk FHIR resource types this drop happens to carry are loaded after
    # the comma-separated files, because each one is patient-scoped.
    for file_name in (*DATASET_FILES, *fhir_files_present(source_uri)):
        try:
            result = _load_file(
                run_id,
                file_name,
                source_uri=source_uri,
                dataset_version=dataset_version,
                ids=ids,
            )
        except MissingColumnError as exc:
            failed = True
            _progress(
                run_id,
                file_name,
                status="fail",
                rows_loaded=0,
                rows_rejected=0,
                provenance_failures=0,
                error_detail=str(exc),
            )
            continue
        except Exception as exc:  # noqa: BLE001 -- any failure names the file, loads nothing
            failed = True
            _progress(
                run_id,
                file_name,
                status="fail",
                rows_loaded=0,
                rows_rejected=0,
                provenance_failures=0,
                error_detail=f"{file_name}: {exc}",
            )
            continue
        if file_name == "patients.csv":
            patient_count = result["rows_loaded"]
        _progress(run_id, file_name, **result)

    status = "failed" if failed else "succeeded"
    _run_state(
        run_id,
        status=status,
        patient_count=patient_count,
        finished_at=datetime.now(UTC),
    )
    return {"run_id": run_id, "status": status, "patient_count": patient_count}


def active_run_ids() -> set[str] | None:
    """The run ids that still have a job queued or started on the ingest queue.

    `None` means the queue could not be read at all, which is never evidence
    that a run is finished: the caller then falls back to the age of the row.
    A run whose job has crashed, been reaped or lost its Redis keys appears in
    neither place, so it is no longer live and must not pin ingest shut.
    """
    try:
        import redis
        from rq import Queue
        from rq.job import Job
        from rq.registry import StartedJobRegistry

        connection = redis.from_url(os.environ["REDIS_URL"])
        queue = Queue("ingest", connection=connection)
        jobs = list(queue.jobs)
        for job_id in StartedJobRegistry(queue=queue).get_job_ids():
            try:
                jobs.append(Job.fetch(job_id, connection=connection))
            except Exception:  # noqa: BLE001 -- a job that vanished mid-read is not live
                continue
    except Exception:  # noqa: BLE001 -- an unreadable queue tells us nothing
        return None
    return {str(job.args[0]) for job in jobs if job is not None and job.args}


def enqueue_ingest(
    run_id: str, dataset_version: str, source_uri: str, seed: int | None = None
) -> str:
    """Queue the job on the project's Redis queue and return its job id."""
    import redis
    from rq import Queue

    queue = Queue("ingest", connection=redis.from_url(os.environ["REDIS_URL"]))
    job = queue.enqueue(run_ingest, run_id, dataset_version, source_uri, seed, job_timeout=3600)
    return job.id
