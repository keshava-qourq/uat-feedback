"""A dataset drop built for the de-duplication criteria (US-004: AC-011..AC-013).

The de-duplication criteria need a cohort whose encounter truth the test
knows, so this drop supplies exactly three true encounters:

* `merged`: one real encounter recorded twice -- once by an EHR source and
  once by a claim source, the same `encounter_ref` at the same time. The
  unified timeline must show it as one entry tagged with both sources and
  count the visit once (AC-011).
* `single`: one real encounter recorded once, by an EHR source only.
* `invisible`: a true encounter present in encounter_truth.csv with
  `visible_in_sources` false and no EHR or claim row at all. It must be
  counted as invisible care and never appear anywhere (AC-013).

So for this drop the de-duplication report must state
`true_encounters` 3, `matched_to_one_entry` 2, `split_into_more_than_one` 0,
`merged_in_error` 0 and `invisible_care` 1 (AC-012).

Every id, display string and persona key carries a per-run suffix, so the drop
belongs to the one module that built it and never collides with another run's
cohort in the shared database. Only the files the ingest job reads are
written, in exactly the formats the dataset ships in.
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

#: What the report must state for this drop (AC-012).
EXPECTED_REPORT: dict[str, int] = {
    "true_encounters": 3,
    "matched_to_one_entry": 2,
    "split_into_more_than_one": 0,
    "merged_in_error": 0,
    "invisible_care": 1,
}

#: The keys the contract says the result carries.
REPORT_KEYS = (
    "true_encounters",
    "matched_to_one_entry",
    "split_into_more_than_one",
    "merged_in_error",
    "invisible_care",
    "dataset_version",
)


def _csv(columns: tuple[str, ...], rows: list[dict[str, str]]) -> bytes:
    buffer = io.StringIO()
    writer = DictWriter(buffer, fieldnames=list(columns), lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({column: row.get(column, "") for column in columns})
    return buffer.getvalue().encode()


def _event(**values: str) -> dict[str, str]:
    return {column: values.get(column, "") for column in EVENT_COLUMNS}


class DedupDrop:
    """One dataset drop whose encounter truth the test knows row by row."""

    def __init__(self, suffix: str) -> None:
        self.suffix = suffix
        self.dataset_version = f"qa-dedup-{suffix}"
        self.merged_patient = f"DDMERGE-{suffix}"
        self.single_patient = f"DDSINGLE-{suffix}"
        self.patient_ids = (self.merged_patient, self.single_patient)

        # The encounter recorded in both an EHR and a claim source (AC-011).
        self.merged_encounter_ref = f"ENCM-{suffix}"
        self.merged_time = "2019-03-04T09:00:00Z"
        self.merged_date = "2019-03-04"
        self.merged_ehr_display = f"Back pain visit EHR {suffix}"
        self.merged_claim_display = f"Back pain visit claim {suffix}"
        self.merged_ehr_ref = f"ehr:enc:{suffix}:m"
        self.merged_claim_ref = f"claim:line:{suffix}:m"

        # The encounter one source recorded once.
        self.single_encounter_ref = f"ENCS-{suffix}"
        self.single_time = "2019-05-05T10:00:00Z"
        self.single_display = f"Physiotherapy visit {suffix}"

        # The true encounter no source contains at all (AC-013).
        self.invisible_encounter_id = f"TINVIS-{suffix}"
        self.invisible_time = "2019-06-06T09:00:00Z"
        self.invisible_date = "2019-06-06"

        self.true_encounter_ids = {
            "merged": f"TMERGE-{suffix}",
            "single": f"TSINGLE-{suffix}",
            "invisible": self.invisible_encounter_id,
        }

        #: Every cutoff is far in the future, so nothing in this drop is hidden
        #: by the leakage guarantee and a missing entry means a missing entry.
        self.cutoff = "2030-01-01"

    # --------------------------------------------------------------- the files

    def _events(self) -> list[dict[str, str]]:
        return [
            _event(
                patient_id=self.merged_patient,
                event_id=f"EM-EHR-{self.suffix}",
                event_time=self.merged_time,
                event_type="encounter",
                code_system="SNOMED",
                code="1",
                display=self.merged_ehr_display,
                provider_org="Clinic A",
                provider_specialty="primary_care",
                source_type="ehr",
                source_ref=self.merged_ehr_ref,
                encounter_ref=self.merged_encounter_ref,
                confidence="0.9",
            ),
            _event(
                patient_id=self.merged_patient,
                event_id=f"EM-CLAIM-{self.suffix}",
                event_time=self.merged_time,
                event_type="encounter",
                code_system="ICD10",
                code="M54.5",
                display=self.merged_claim_display,
                provider_org="Clinic A",
                provider_specialty="primary_care",
                source_type="claim",
                source_ref=self.merged_claim_ref,
                encounter_ref=self.merged_encounter_ref,
                confidence="0.8",
            ),
            _event(
                patient_id=self.single_patient,
                event_id=f"ES-EHR-{self.suffix}",
                event_time=self.single_time,
                event_type="encounter",
                code_system="SNOMED",
                code="2",
                display=self.single_display,
                provider_org="Clinic C",
                provider_specialty="physiotherapy",
                source_type="ehr",
                source_ref=f"ehr:enc:{self.suffix}:s",
                encounter_ref=self.single_encounter_ref,
                confidence="0.9",
            ),
        ]

    def files(self) -> dict[str, bytes]:
        merged, single = self.merged_patient, self.single_patient
        patients = _csv(
            ("patient_id", "display_name", "birth_year", "sex", "reachable_history_start"),
            [
                {
                    "patient_id": merged,
                    "display_name": f"Dedup Merge {self.suffix}",
                    "birth_year": "1981",
                    "sex": "F",
                    "reachable_history_start": "2016-01-01",
                },
                {
                    "patient_id": single,
                    "display_name": f"Dedup Single {self.suffix}",
                    "birth_year": "1975",
                    "sex": "M",
                    "reachable_history_start": "2015-06-01",
                },
            ],
        )
        labels = _csv(
            (
                "patient_id",
                "eval_cutoff_date",
                "split",
                "archetype",
                "typicality",
                "clue_density",
                "hla_b27_true",
                "axspa_label",
                "simulated_diagnosis_date",
            ),
            [
                {
                    "patient_id": pid,
                    "eval_cutoff_date": self.cutoff,
                    "split": split,
                    "archetype": "classic",
                    "typicality": "typical",
                    "clue_density": "0.5",
                    "hla_b27_true": "true",
                    "axspa_label": "true",
                    "simulated_diagnosis_date": "",
                }
                for pid, split in ((merged, "train"), (single, "test"))
            ],
        )
        notes = _csv(
            ("patient_id", "source_ref", "note_time", "note_type", "text"),
            [
                {
                    "patient_id": merged,
                    "source_ref": self.merged_ehr_ref,
                    "note_time": self.merged_time,
                    "note_type": "clinic_note",
                    "text": f"Back pain reviewed in clinic {self.suffix}.",
                }
            ],
        )
        intake = _csv(
            ("patient_id", "question_key", "answer_value", "answered_at", "is_complete"),
            [
                {
                    "patient_id": merged,
                    "question_key": "morning_stiffness_minutes",
                    "answer_value": "75",
                    "answered_at": "2020-01-02T10:00:00Z",
                    "is_complete": "true",
                }
            ],
        )
        coverage = _csv(
            ("patient_id", "payer", "start_date", "end_date", "gap_reason"),
            [
                {
                    "patient_id": merged,
                    "payer": "Payer One",
                    "start_date": "2016-01-01",
                    "end_date": "2020-12-31",
                }
            ],
        )
        truth = _csv(
            ("patient_id", "true_encounter_id", "encounter_time", "visible_in_sources"),
            [
                {
                    "patient_id": merged,
                    "true_encounter_id": self.true_encounter_ids["merged"],
                    "encounter_time": self.merged_time,
                    "visible_in_sources": "true",
                },
                {
                    "patient_id": single,
                    "true_encounter_id": self.true_encounter_ids["single"],
                    "encounter_time": self.single_time,
                    "visible_in_sources": "true",
                },
                {
                    "patient_id": merged,
                    "true_encounter_id": self.invisible_encounter_id,
                    "encounter_time": self.invisible_time,
                    "visible_in_sources": "false",
                },
            ],
        )
        heroes = json.dumps(
            [
                {
                    "persona_key": f"dedup-{self.suffix}",
                    "name": f"Dedup Merge {self.suffix}",
                    "one_line_description": "De-duplication fixture persona.",
                    "patient_id": merged,
                    "cutoff_date": self.cutoff,
                }
            ]
        ).encode()

        return {
            "patients.csv": patients,
            "labels.csv": labels,
            "events.csv": _csv(EVENT_COLUMNS, self._events()),
            "notes.csv": notes,
            "intake.csv": intake,
            "coverage.csv": coverage,
            "encounter_truth.csv": truth,
            "heroes.json": heroes,
        }
