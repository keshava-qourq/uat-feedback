"""A dataset drop built for the provenance criteria (US-002: AC-005..AC-007).

The general ingest fixtures in `fixtures_dataset.py` are shaped around the
per-file row counts US-001 checks, so provenance gets its own small drop here
instead of bending those. Two things it adds:

* an event whose `source_ref` is exactly the `source_ref` of a row in
  notes.csv, for both an `ehr` note and a `patient`-sourced note (AC-006);
* on request, one events.csv row with an empty `source_ref` and one with an
  empty `source_type` (AC-007).

Every dataset patient id, persona key and display name carries a per-run
suffix, so a drop belongs to the one test that built it and never collides
with another run's cohort in the shared database.

Only the files the job needs are written: comma-separated files and
heroes.json, in exactly the formats the dataset ships in. No FHIR files, so
nothing here depends on another story's resource types.
"""

from __future__ import annotations

import io
import json
from csv import DictWriter

EVENT_COLUMNS = (
    "patient_id",
    "event_id",
    "event_time",
    "event_type",
    "code_system",
    "code",
    "display",
    "value",
    "unit",
    "provider_org",
    "provider_specialty",
    "source_type",
    "source_ref",
    "encounter_ref",
    "confidence",
)

#: The fields AC-005 requires every stored event to carry.
AC005_FIELDS = EVENT_COLUMNS

#: The sixteenth stored provenance field: which load the row came from, or the
#: row's own server-generated id (both are in the `events` schema).
AC005_SIXTEENTH = ("dataset_version", "id", "encounter_id")


def _csv(columns: tuple[str, ...], rows: list[dict[str, str]]) -> bytes:
    buffer = io.StringIO()
    writer = DictWriter(buffer, fieldnames=list(columns), lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({column: row.get(column, "") for column in columns})
    return buffer.getvalue().encode()


def _event(**values: str) -> dict[str, str]:
    return {column: values.get(column, "") for column in EVENT_COLUMNS}


class ProvenanceDrop:
    """One dataset drop and everything a test needs to recognise it again."""

    def __init__(self, suffix: str, *, with_bad_rows: bool = False) -> None:
        self.suffix = suffix
        self.with_bad_rows = with_bad_rows
        self.patient_ids = (f"PA-{suffix}", f"PB-{suffix}", f"PC-{suffix}")
        a, b, c = self.patient_ids

        #: source_ref -> the note text notes.csv carries for it
        self.note_texts: dict[str, str] = {
            f"ehr:note:{suffix}:1": "Reports morning stiffness lasting over an hour.",
            f"patient:note:{suffix}:2": "Patient describes night pain that wakes them at 4am.",
        }
        self.ehr_note_ref = f"ehr:note:{suffix}:1"
        self.patient_note_ref = f"patient:note:{suffix}:2"

        self.good_events: list[dict[str, str]] = [
            _event(
                patient_id=a,
                event_id=f"E1-{suffix}",
                event_time="2018-04-02T09:00:00Z",
                event_type="encounter",
                code_system="SNOMED",
                code="1",
                display="Back pain visit",
                value="1",
                unit="visit",
                provider_org="Clinic A",
                provider_specialty="primary_care",
                source_type="ehr",
                source_ref=f"ehr:enc:{suffix}:1",
                encounter_ref=f"ENC1-{suffix}",
                confidence="0.9",
            ),
            # Derived from a free-text clinic note (AC-006, source_type ehr).
            _event(
                patient_id=a,
                event_id=f"E2-{suffix}",
                event_time="2018-04-02T09:30:00Z",
                event_type="note",
                code_system="SNOMED",
                code="2",
                display="Clinic note",
                value="text",
                unit="note",
                provider_org="Clinic A",
                provider_specialty="primary_care",
                source_type="ehr",
                source_ref=self.ehr_note_ref,
                encounter_ref=f"ENC1-{suffix}",
                confidence="0.8",
            ),
            # Derived from a patient-reported note (AC-006, source_type patient).
            _event(
                patient_id=c,
                event_id=f"E3-{suffix}",
                event_time="2020-02-20T09:00:00Z",
                event_type="note",
                code_system="SNOMED",
                code="3",
                display="Patient note",
                value="text",
                unit="note",
                provider_org="Clinic C",
                provider_specialty="physiotherapy",
                source_type="patient",
                source_ref=self.patient_note_ref,
                encounter_ref=f"ENC3-{suffix}",
                confidence="0.7",
            ),
            _event(
                patient_id=b,
                event_id=f"E4-{suffix}",
                event_time="2019-07-11T14:30:00Z",
                event_type="claim_line",
                code_system="ICD10",
                code="M54.5",
                display="Low back pain",
                value="1",
                unit="line",
                provider_org="Clinic B",
                provider_specialty="rheumatology",
                source_type="claim",
                source_ref=f"claim:line:{suffix}:4",
                encounter_ref=f"ENC2-{suffix}",
                confidence="0.6",
            ),
        ]

        # AC-007: one row with no source_ref, one row with no source_type.
        self.missing_source_ref_event_id = f"X-NOREF-{suffix}"
        self.missing_source_type_event_id = f"X-NOTYPE-{suffix}"
        self.missing_source_ref_display = f"Provenance gap no source ref {suffix}"
        self.missing_source_type_display = f"Provenance gap no source type {suffix}"
        self.bad_events: list[dict[str, str]] = [
            _event(
                patient_id=a,
                event_id=self.missing_source_ref_event_id,
                event_time="2018-05-01T09:00:00Z",
                event_type="encounter",
                code_system="SNOMED",
                code="9",
                display=self.missing_source_ref_display,
                provider_org="Clinic A",
                provider_specialty="primary_care",
                source_type="ehr",
                source_ref="",
                encounter_ref=f"ENC9-{suffix}",
                confidence="0.5",
            ),
            _event(
                patient_id=b,
                event_id=self.missing_source_type_event_id,
                event_time="2019-08-01T09:00:00Z",
                event_type="lab",
                code_system="LOINC",
                code="1988-5",
                display=self.missing_source_type_display,
                value="12",
                unit="mg/L",
                provider_org="Clinic B",
                provider_specialty="rheumatology",
                source_type="",
                source_ref=f"ehr:obs:{suffix}:91",
                encounter_ref=f"ENC8-{suffix}",
                confidence="0.5",
            ),
        ]

    # --------------------------------------------------------------- the files

    @property
    def events(self) -> list[dict[str, str]]:
        return [*self.good_events, *(self.bad_events if self.with_bad_rows else [])]

    def files(self) -> dict[str, bytes]:
        a, b, c = self.patient_ids
        patients = _csv(
            ("patient_id", "display_name", "birth_year", "sex", "reachable_history_start"),
            [
                {
                    "patient_id": a,
                    "display_name": f"Ada Prov {self.suffix}",
                    "birth_year": "1981",
                    "sex": "F",
                    "reachable_history_start": "2016-01-01",
                },
                {
                    "patient_id": b,
                    "display_name": f"Grace Prov {self.suffix}",
                    "birth_year": "1975",
                    "sex": "F",
                    "reachable_history_start": "2015-06-01",
                },
                {
                    "patient_id": c,
                    "display_name": f"Alan Prov {self.suffix}",
                    "birth_year": "1990",
                    "sex": "M",
                    "reachable_history_start": "2017-03-01",
                },
            ],
        )
        labels = _csv(
            ("patient_id", "eval_cutoff_date", "split", "archetype", "axspa_label"),
            [
                {
                    "patient_id": pid,
                    "eval_cutoff_date": "2023-01-01",
                    "split": split,
                    "archetype": "classic",
                    "axspa_label": "true",
                }
                for pid, split in zip(self.patient_ids, ("train", "val", "test"), strict=True)
            ],
        )
        notes = _csv(
            ("patient_id", "source_ref", "note_time", "note_type", "text"),
            [
                {
                    "patient_id": a,
                    "source_ref": self.ehr_note_ref,
                    "note_time": "2018-04-02T09:30:00Z",
                    "note_type": "clinic_note",
                    "text": self.note_texts[self.ehr_note_ref],
                },
                {
                    "patient_id": c,
                    "source_ref": self.patient_note_ref,
                    "note_time": "2020-02-20T09:00:00Z",
                    "note_type": "imaging_report",
                    "text": self.note_texts[self.patient_note_ref],
                },
            ],
        )
        intake = _csv(
            ("patient_id", "question_key", "answer_value", "answered_at", "is_complete"),
            [
                {
                    "patient_id": a,
                    "question_key": "morning_stiffness_minutes",
                    "answer_value": "75",
                    "answered_at": "2021-01-02T10:00:00Z",
                    "is_complete": "true",
                }
            ],
        )
        coverage = _csv(
            ("patient_id", "payer", "start_date", "end_date", "gap_reason"),
            [
                {
                    "patient_id": a,
                    "payer": "Payer One",
                    "start_date": "2016-01-01",
                    "end_date": "2018-12-31",
                }
            ],
        )
        truth = _csv(
            ("patient_id", "true_encounter_id", "encounter_time", "visible_in_sources"),
            [
                {
                    "patient_id": a,
                    "true_encounter_id": f"T1-{self.suffix}",
                    "encounter_time": "2018-04-02T09:00:00Z",
                    "visible_in_sources": "true",
                }
            ],
        )
        heroes = json.dumps(
            [
                {
                    "persona_key": f"prov-ada-{self.suffix}",
                    "name": f"Ada Prov {self.suffix}",
                    "one_line_description": "Provenance fixture persona.",
                    "patient_id": a,
                    "cutoff_date": "2023-01-01",
                }
            ]
        ).encode()

        return {
            "patients.csv": patients,
            "labels.csv": labels,
            "events.csv": _csv(EVENT_COLUMNS, self.events),
            "notes.csv": notes,
            "intake.csv": intake,
            "coverage.csv": coverage,
            "encounter_truth.csv": truth,
            "heroes.json": heroes,
        }
