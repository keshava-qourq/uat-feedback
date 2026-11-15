"""A tiny stand-in for dataset v0.1, in exactly the formats the dataset ships in.

One patient-sized slice of every file the ingest must read (AC-001, NFR-023):
comma-separated files, `heroes.json`, and gzipped bulk FHIR newline-delimited
JSON per resource type. Nothing here is converted by hand first -- the bytes
written are the bytes a real dataset drop would contain.

The files are written through the application's own storage module, so the
same helper works against the sandbox's S3 bucket and against a disk
`MEDIA_ROOT`, and `source_uri` names the directory the ingest is pointed at.
"""

from __future__ import annotations

import gzip
import json
import os
import uuid
from pathlib import Path

from app import storage

PATIENT_IDS = ("P0001", "P0002", "P0003")

PATIENTS_CSV = (
    "patient_id,display_name,birth_year,sex,reachable_history_start\n"
    "P0001,Ada Lovelace,1981,F,2016-01-01\n"
    "P0002,Grace Hopper,1975,F,2015-06-01\n"
    "P0003,Alan Turing,1990,M,2017-03-01\n"
)

LABELS_CSV = (
    "patient_id,eval_cutoff_date,split,archetype,typicality,clue_density,"
    "hla_b27_true,axspa_label,simulated_diagnosis_date\n"
    "P0001,2021-01-01,train,classic,typical,0.80,true,true,2021-06-01\n"
    "P0002,2021-01-01,val,mechanical_lookalike,atypical,0.20,false,false,\n"
    "P0003,2021-01-01,test,classic,typical,0.60,true,true,2022-02-01\n"
)

EVENTS_CSV = (
    "patient_id,event_id,event_time,event_type,code_system,code,display,value,unit,"
    "provider_org,provider_specialty,source_type,source_ref,encounter_ref,confidence\n"
    "P0001,E1,2018-04-02T09:00:00Z,encounter,SNOMED,1,Back pain visit,,,Clinic A,"
    "primary_care,ehr,ehr:enc:1,ENC1,0.9\n"
    "P0001,E2,2018-04-02T09:00:00Z,claim_line,ICD10,M54.5,Low back pain,,,Clinic A,"
    "primary_care,claim,claim:line:1,ENC1,0.8\n"
    "P0002,E3,2019-07-11T14:30:00Z,lab,LOINC,1988-5,CRP,12,mg/L,Clinic B,rheumatology,"
    "ehr,ehr:obs:3,ENC2,0.95\n"
    "P0003,E4,2020-02-20T08:15:00Z,encounter,SNOMED,2,Physio visit,,,Clinic C,"
    "physiotherapy,ehr,ehr:enc:4,ENC3,0.9\n"
)

NOTES_CSV = (
    "patient_id,source_ref,note_time,note_type,text\n"
    "P0001,ehr:note:1,2018-04-02T09:30:00Z,clinic_note,"
    '"Reports morning stiffness lasting over an hour."\n'
    "P0003,ehr:note:2,2020-02-20T09:00:00Z,imaging_report,"
    '"Sacroiliac joints unremarkable on radiograph."\n'
)

INTAKE_CSV = (
    "patient_id,question_key,answer_value,answered_at,is_complete\n"
    "P0001,morning_stiffness_minutes,75,2021-01-02T10:00:00Z,true\n"
    "P0002,morning_stiffness_minutes,5,2021-01-02T10:05:00Z,true\n"
)

COVERAGE_CSV = (
    "patient_id,payer,start_date,end_date,gap_reason\n"
    "P0001,Payer One,2016-01-01,2018-12-31,\n"
    "P0001,,2019-01-01,2019-03-31,between_insurers\n"
    "P0002,Payer Two,2015-06-01,2022-12-31,\n"
)

ENCOUNTER_TRUTH_CSV = (
    "patient_id,true_encounter_id,encounter_time,visible_in_sources\n"
    "P0001,T1,2018-04-02T09:00:00Z,true\n"
    "P0002,T2,2019-07-11T14:30:00Z,true\n"
    "P0003,T3,2020-02-20T08:15:00Z,true\n"
    "P0003,T4,2020-09-09T08:15:00Z,false\n"
)

HEROES_JSON = json.dumps(
    [
        {
            "persona_key": "ada-classic",
            "name": "Ada Lovelace",
            "one_line_description": "Classic presentation missed for years.",
            "patient_id": "P0001",
            "cutoff_date": "2021-01-01",
        },
        {
            "persona_key": "grace-lookalike",
            "name": "Grace Hopper",
            "one_line_description": "Mechanical look-alike that should stay low.",
            "patient_id": "P0002",
            "cutoff_date": "2021-01-01",
        },
    ]
).encode()


def _ndjson_gz(lines: list[dict]) -> bytes:
    body = "\n".join(json.dumps(line) for line in lines) + "\n"
    return gzip.compress(body.encode())


FHIR_FILES: dict[str, bytes] = {
    "fhir/Patient.ndjson.gz": _ndjson_gz(
        [
            {"resourceType": "Patient", "id": "P0001", "gender": "female"},
            {"resourceType": "Patient", "id": "P0002", "gender": "female"},
            {"resourceType": "Patient", "id": "P0003", "gender": "male"},
        ]
    ),
    "fhir/Condition.ndjson.gz": _ndjson_gz(
        [
            {
                "resourceType": "Condition",
                "id": "C1",
                "subject": {"reference": "Patient/P0001"},
                "code": {"coding": [{"system": "http://hl7.org/fhir/sid/icd-10", "code": "M54.5"}]},
                "recordedDate": "2018-04-02",
            }
        ]
    ),
    "fhir/Observation.ndjson.gz": _ndjson_gz(
        [
            {
                "resourceType": "Observation",
                "id": "O1",
                "subject": {"reference": "Patient/P0002"},
                "code": {"coding": [{"system": "http://loinc.org", "code": "1988-5"}]},
                "effectiveDateTime": "2019-07-11T14:30:00Z",
                "valueQuantity": {"value": 12, "unit": "mg/L"},
            }
        ]
    ),
}

# rows per comma-separated file, header excluded -- what the per-file report must say
EXPECTED_ROWS: dict[str, int] = {
    "patients.csv": 3,
    "labels.csv": 3,
    "events.csv": 4,
    "notes.csv": 2,
    "intake.csv": 2,
    "coverage.csv": 3,
    "encounter_truth.csv": 4,
}

CSV_FILES: dict[str, bytes] = {
    "patients.csv": PATIENTS_CSV.encode(),
    "labels.csv": LABELS_CSV.encode(),
    "events.csv": EVENTS_CSV.encode(),
    "notes.csv": NOTES_CSV.encode(),
    "intake.csv": INTAKE_CSV.encode(),
    "coverage.csv": COVERAGE_CSV.encode(),
    "encounter_truth.csv": ENCOUNTER_TRUTH_CSV.encode(),
}


def fixture_set(**overrides: bytes) -> dict[str, bytes]:
    """Every dataset file, with any named file replaced by `overrides`."""
    files: dict[str, bytes] = {**CSV_FILES, "heroes.json": HEROES_JSON, **FHIR_FILES}
    files.update(overrides)
    return files


def events_csv_missing_source_ref() -> bytes:
    """events.csv with the required `source_ref` column dropped (AC-003)."""
    rows = [line.split(",") for line in EVENTS_CSV.strip().split("\n")]
    drop = rows[0].index("source_ref")
    kept = "\n".join(",".join(c for i, c in enumerate(r) if i != drop) for r in rows)
    return (kept + "\n").encode()


def upload_fixture_set(files: dict[str, bytes]) -> tuple[str, str]:
    """Write `files` to the storage the application reads.

    Returns `(source_uri, prefix)`: the location to hand to
    POST /api/admin/ingest-runs, and the storage key prefix the files sit
    under so a test can delete them again.
    """
    prefix = f"ingest-fixtures/{uuid.uuid4()}"
    for name, data in files.items():
        storage.save_bytes(f"{prefix}/{name}", data)
    bucket = os.getenv("S3_BUCKET")
    if bucket:
        return f"s3://{bucket}/{prefix}", prefix
    root = Path(os.getenv("MEDIA_ROOT", storage.DEFAULT_MEDIA_ROOT))
    return str(root / prefix), prefix


def delete_fixture_set(prefix: str, files: dict[str, bytes]) -> None:
    for name in files:
        storage.delete(f"{prefix}/{name}")
