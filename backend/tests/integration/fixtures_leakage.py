"""A dataset drop built for the leakage guarantee (US-003: AC-008..AC-010, AC-028,
AC-029, NFR-013).

The leakage criteria need a cohort whose ground truth is known to the test:
a confirmed case whose evaluation cutoff falls thirty days *before* its
diagnosis, a look-alike that is not a case, post-cutoff items that must never
be rendered, and an undated family-history row -- the one exception the
non-functional requirement allows.

Every ground-truth value carries a per-run marker string, so a scan of a
rendered payload can say exactly which field leaked and for which patient
instead of guessing at a generic word like "classic".

Only the files the ingest job reads are produced, in the formats the dataset
ships in.
"""

from __future__ import annotations

import io
import json
from csv import DictWriter
from datetime import date, timedelta

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

LABEL_COLUMNS = (
    "patient_id",
    "eval_cutoff_date",
    "split",
    "archetype",
    "typicality",
    "clue_density",
    "hla_b27_true",
    "axspa_label",
    "simulated_diagnosis_date",
)

#: The label columns that are ground truth: none of them may reach a scoring
#: input, a feature or anything rendered for a patient (AC-008, AC-010).
GROUND_TRUTH_COLUMNS = (
    "archetype",
    "typicality",
    "clue_density",
    "hla_b27_true",
    "axspa_label",
    "simulated_diagnosis_date",
)

#: The only two label columns that may reach the engine or the demo path (AC-010).
OPERATIONAL_COLUMNS = ("eval_cutoff_date", "split")

CUTOFF = date(2021, 1, 1)
DIAGNOSIS = CUTOFF + timedelta(days=30)


def _csv(columns: tuple[str, ...], rows: list[dict[str, str]]) -> bytes:
    buffer = io.StringIO()
    writer = DictWriter(buffer, fieldnames=list(columns), lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({column: row.get(column, "") for column in columns})
    return buffer.getvalue().encode()


def _event(**values: str) -> dict[str, str]:
    return {column: values.get(column, "") for column in EVENT_COLUMNS}


class LeakageDrop:
    """One dataset drop whose ground truth and post-cutoff items the test knows."""

    def __init__(self, suffix: str) -> None:
        self.suffix = suffix
        self.case_id = f"LKCASE-{suffix}"
        self.lookalike_id = f"LKLOOK-{suffix}"
        self.patient_ids = (self.case_id, self.lookalike_id)
        self.cutoff = CUTOFF
        self.diagnosis_date = DIAGNOSIS
        self.persona_key = f"leak-case-{suffix}"

        #: dataset patient id -> its evaluation cutoff
        self.cutoffs: dict[str, date] = {
            self.case_id: CUTOFF,
            self.lookalike_id: CUTOFF,
        }

        #: The ground-truth values this drop supplies, marked per run so a leak
        #: is unambiguous. Values, not just column names, are scanned for.
        self.ground_truth: dict[str, dict[str, str]] = {
            self.case_id: {
                "archetype": f"archetype-classic-{suffix}",
                "typicality": f"typicality-typical-{suffix}",
                "clue_density": "0.77",
                "hla_b27_true": "true",
                "axspa_label": "true",
                "simulated_diagnosis_date": DIAGNOSIS.isoformat(),
            },
            self.lookalike_id: {
                "archetype": f"archetype-mechanical-{suffix}",
                "typicality": f"typicality-atypical-{suffix}",
                "clue_density": "0.11",
                "hla_b27_true": "false",
                "axspa_label": "false",
                "simulated_diagnosis_date": "",
            },
        }

        #: Items dated on or after the cutoff: display text -> its date.
        self.post_cutoff_items: dict[str, str] = {
            f"Diagnosis confirmed at rheumatology {suffix}": DIAGNOSIS.isoformat(),
            f"Rheumatology workup sacroiliac imaging {suffix}": "2021-01-10",
            f"Rheumatology workup inflammatory marker {suffix}": "2021-01-05",
            f"Item dated exactly on the cutoff {suffix}": CUTOFF.isoformat(),
        }
        self.diagnosis_display = f"Diagnosis confirmed at rheumatology {suffix}"
        self.workup_displays = (
            f"Rheumatology workup sacroiliac imaging {suffix}",
            f"Rheumatology workup inflammatory marker {suffix}",
        )
        self.on_cutoff_display = f"Item dated exactly on the cutoff {suffix}"
        self.pre_cutoff_display = f"Back pain primary care visit {suffix}"
        self.undated_family_history_display = f"Family history of axial disease {suffix}"

    # --------------------------------------------------------------- the files

    def _events(self) -> list[dict[str, str]]:
        case, look = self.case_id, self.lookalike_id
        rows = [
            _event(
                patient_id=case,
                event_id=f"PRE-{self.suffix}",
                event_time="2019-04-02T09:00:00Z",
                event_type="encounter",
                code_system="SNOMED",
                code="1",
                display=self.pre_cutoff_display,
                provider_org="Clinic A",
                provider_specialty="primary_care",
                source_type="ehr",
                source_ref=f"ehr:enc:{self.suffix}:1",
                encounter_ref=f"ENC1-{self.suffix}",
                confidence="0.9",
            ),
            # The undated family-history row: the one exception NFR-013 allows.
            _event(
                patient_id=case,
                event_id=f"FAM-{self.suffix}",
                event_time="",
                event_type="family_history",
                code_system="SNOMED",
                code="2",
                display=self.undated_family_history_display,
                provider_org="Clinic A",
                provider_specialty="primary_care",
                source_type="patient",
                source_ref=f"patient:fh:{self.suffix}:1",
                encounter_ref="",
                confidence="0.6",
            ),
            _event(
                patient_id=look,
                event_id=f"PRE2-{self.suffix}",
                event_time="2019-07-11T14:30:00Z",
                event_type="lab",
                code_system="LOINC",
                code="1988-5",
                display=f"Inflammatory marker {self.suffix}",
                value="3",
                unit="mg/L",
                provider_org="Clinic B",
                provider_specialty="primary_care",
                source_type="ehr",
                source_ref=f"ehr:obs:{self.suffix}:2",
                encounter_ref=f"ENC2-{self.suffix}",
                confidence="0.8",
            ),
        ]
        for index, (display, when) in enumerate(self.post_cutoff_items.items(), start=1):
            rows.append(
                _event(
                    patient_id=case,
                    event_id=f"POST{index}-{self.suffix}",
                    event_time=f"{when}T09:00:00Z",
                    event_type="encounter",
                    code_system="SNOMED",
                    code=str(100 + index),
                    display=display,
                    provider_org="Rheumatology Centre",
                    provider_specialty="rheumatology",
                    source_type="ehr",
                    source_ref=f"ehr:enc:{self.suffix}:post{index}",
                    encounter_ref=f"ENCP{index}-{self.suffix}",
                    confidence="0.9",
                )
            )
        return rows

    def files(self) -> dict[str, bytes]:
        case, look = self.case_id, self.lookalike_id
        patients = _csv(
            ("patient_id", "display_name", "birth_year", "sex", "reachable_history_start"),
            [
                {
                    "patient_id": case,
                    "display_name": f"Leak Case {self.suffix}",
                    "birth_year": "1981",
                    "sex": "F",
                    "reachable_history_start": "2016-01-01",
                },
                {
                    "patient_id": look,
                    "display_name": f"Leak Lookalike {self.suffix}",
                    "birth_year": "1975",
                    "sex": "M",
                    "reachable_history_start": "2015-06-01",
                },
            ],
        )
        labels = _csv(
            LABEL_COLUMNS,
            [
                {
                    "patient_id": pid,
                    "eval_cutoff_date": self.cutoffs[pid].isoformat(),
                    "split": split,
                    **self.ground_truth[pid],
                }
                for pid, split in ((case, "test"), (look, "train"))
            ],
        )
        notes = _csv(
            ("patient_id", "source_ref", "note_time", "note_type", "text"),
            [
                {
                    "patient_id": case,
                    "source_ref": f"ehr:enc:{self.suffix}:1",
                    "note_time": "2019-04-02T09:30:00Z",
                    "note_type": "clinic_note",
                    "text": f"Morning stiffness over an hour {self.suffix}.",
                },
                {
                    "patient_id": case,
                    "source_ref": f"ehr:enc:{self.suffix}:post1",
                    "note_time": f"{self.diagnosis_date.isoformat()}T09:30:00Z",
                    "note_type": "clinic_note",
                    "text": self.diagnosis_display,
                },
            ],
        )
        intake = _csv(
            ("patient_id", "question_key", "answer_value", "answered_at", "is_complete"),
            [
                {
                    "patient_id": case,
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
                    "patient_id": case,
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
                    "patient_id": case,
                    "true_encounter_id": f"T1-{self.suffix}",
                    "encounter_time": "2019-04-02T09:00:00Z",
                    "visible_in_sources": "true",
                }
            ],
        )
        heroes = json.dumps(
            [
                {
                    "persona_key": self.persona_key,
                    "name": f"Leak Case {self.suffix}",
                    "one_line_description": "Leakage fixture persona.",
                    "patient_id": case,
                    "cutoff_date": self.cutoff.isoformat(),
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
