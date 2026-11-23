"""A dataset drop built for the clue-extraction criteria (US-015: AC-049..AC-052).

Two patients, two notes, and nothing else the criteria do not need:

* `clues`: an imaging report whose sentences carry, one per sentence, each of
  the pack's target clues AC-049 names -- sacroiliitis wording, iliac-side-only
  sclerosis, the absence of erosions and postpartum timing. Because each clue
  sits in its own sentence, "the exact quoted sentence" of a finding can be
  compared byte for byte with the sentence the clue came from.
* `clean`: a clinic note with none of those clues at all, which must yield no
  finding yet still be recorded as processed (AC-050).

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

#: The four target clues AC-049 names, as (a short name for the assertion
#: message, the words that must appear in the quoted sentence).
TARGET_CLUES: dict[str, tuple[str, ...]] = {
    "sacroiliitis": ("sacroiliitis",),
    "iliac_side_sclerosis": ("sclerosis", "iliac"),
    "erosions": ("erosion",),
    "postpartum_timing": ("postpartum",),
}

#: Where a finding's quoted sentence may arrive in a payload.
QUOTE_KEYS = ("quoted_sentence", "quote", "quoted_text", "sentence", "evidence_quote")

#: Where a finding's clue type may arrive.
CLUE_TYPE_KEYS = ("clue_type", "clue", "finding_type", "type", "key")

#: Where a finding's reference back to its note may arrive.
NOTE_REF_KEYS = (
    "source_ref",
    "note_source_ref",
    "note_ref",
    "note_id",
    "note_url",
    "note_link",
    "link",
    "full_note_url",
)

#: The keys the extraction report must carry (AC-052).
REPORT_KEYS = ("notes_processed", "findings_by_clue", "caveat")


def _csv(columns: tuple[str, ...], rows: list[dict[str, str]]) -> bytes:
    buffer = io.StringIO()
    writer = DictWriter(buffer, fieldnames=list(columns), lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({column: row.get(column, "") for column in columns})
    return buffer.getvalue().encode()


def _event(**values: str) -> dict[str, str]:
    return {column: values.get(column, "") for column in EVENT_COLUMNS}


class ExtractionDrop:
    """One dataset drop whose note text the test knows sentence by sentence."""

    def __init__(self, suffix: str) -> None:
        self.suffix = suffix
        self.dataset_version = f"qa-extract-{suffix}"
        self.clue_patient = f"EXCLUE-{suffix}"
        self.clean_patient = f"EXCLEAN-{suffix}"
        self.patient_ids = (self.clue_patient, self.clean_patient)

        #: Far in the future, so nothing in this drop is hidden by the leakage
        #: guarantee and a missing finding means a missing finding.
        self.cutoff = "2030-01-01"

        self.imaging_source_ref = f"ehr:note:{suffix}:img"
        self.clean_source_ref = f"ehr:note:{suffix}:clean"
        self.imaging_time = "2019-03-04T09:00:00Z"
        self.clean_time = "2019-05-05T10:00:00Z"

        #: clue name -> the one sentence of the imaging report that carries it.
        self.clue_sentences: dict[str, str] = {
            "sacroiliitis": (
                "MRI of the sacroiliac joints demonstrates active sacroiliitis "
                "with bone marrow oedema."
            ),
            "iliac_side_sclerosis": (
                "Sclerosis is confined to the iliac side of the joint."
            ),
            "erosions": "No erosions are identified.",
            "postpartum_timing": (
                "Symptoms began three months postpartum after her second delivery."
            ),
        }
        self.imaging_text = " ".join(
            self.clue_sentences[name] for name in TARGET_CLUES if name in self.clue_sentences
        )
        self.clean_text = (
            "Attended for a routine medication review. "
            "Seasonal allergy symptoms are well controlled on the current antihistamine. "
            "No new concerns were raised today."
        )

    # --------------------------------------------------------------- the files

    def files(self) -> dict[str, bytes]:
        clue, clean = self.clue_patient, self.clean_patient
        patients = _csv(
            ("patient_id", "display_name", "birth_year", "sex", "reachable_history_start"),
            [
                {
                    "patient_id": clue,
                    "display_name": f"Extract Clue {self.suffix}",
                    "birth_year": "1986",
                    "sex": "F",
                    "reachable_history_start": "2016-01-01",
                },
                {
                    "patient_id": clean,
                    "display_name": f"Extract Clean {self.suffix}",
                    "birth_year": "1979",
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
                for pid, split in ((clue, "train"), (clean, "test"))
            ],
        )
        events = _csv(
            EVENT_COLUMNS,
            [
                _event(
                    patient_id=clue,
                    event_id=f"EX-IMG-{self.suffix}",
                    event_time=self.imaging_time,
                    event_type="imaging",
                    code_system="CPT",
                    code="72195",
                    display=f"MRI sacroiliac joints {self.suffix}",
                    provider_org="Imaging Centre",
                    provider_specialty="radiology",
                    source_type="ehr",
                    source_ref=self.imaging_source_ref,
                    encounter_ref=f"ENCX-{self.suffix}",
                    confidence="0.9",
                ),
                _event(
                    patient_id=clue,
                    event_id=f"EX-BP-{self.suffix}",
                    event_time="2018-02-02T09:00:00Z",
                    event_type="encounter",
                    code_system="ICD-10",
                    code="M54.5",
                    display=f"Back pain visit {self.suffix}",
                    provider_org="Clinic A",
                    provider_specialty="primary_care",
                    source_type="ehr",
                    source_ref=f"ehr:enc:{self.suffix}:1",
                    encounter_ref=f"ENCB-{self.suffix}",
                    confidence="0.9",
                ),
                _event(
                    patient_id=clean,
                    event_id=f"EX-CLEAN-{self.suffix}",
                    event_time=self.clean_time,
                    event_type="encounter",
                    code_system="ICD-10",
                    code="M54.5",
                    display=f"Medication review {self.suffix}",
                    provider_org="Clinic C",
                    provider_specialty="primary_care",
                    source_type="ehr",
                    source_ref=self.clean_source_ref,
                    encounter_ref=f"ENCC-{self.suffix}",
                    confidence="0.9",
                ),
            ],
        )
        notes = _csv(
            ("patient_id", "source_ref", "note_time", "note_type", "text"),
            [
                {
                    "patient_id": clue,
                    "source_ref": self.imaging_source_ref,
                    "note_time": self.imaging_time,
                    "note_type": "imaging_report",
                    "text": self.imaging_text,
                },
                {
                    "patient_id": clean,
                    "source_ref": self.clean_source_ref,
                    "note_time": self.clean_time,
                    "note_type": "clinic_note",
                    "text": self.clean_text,
                },
            ],
        )
        intake = _csv(
            ("patient_id", "question_key", "answer_value", "answered_at", "is_complete"),
            [
                {
                    "patient_id": clue,
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
                    "patient_id": clue,
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
                    "patient_id": clue,
                    "true_encounter_id": f"TX-{self.suffix}",
                    "encounter_time": self.imaging_time,
                    "visible_in_sources": "true",
                },
                {
                    "patient_id": clean,
                    "true_encounter_id": f"TC-{self.suffix}",
                    "encounter_time": self.clean_time,
                    "visible_in_sources": "true",
                },
            ],
        )
        heroes = json.dumps(
            [
                {
                    "persona_key": f"extract-{self.suffix}",
                    "name": f"Extract Clue {self.suffix}",
                    "one_line_description": "Clue-extraction fixture persona.",
                    "patient_id": clue,
                    "cutoff_date": self.cutoff,
                }
            ]
        ).encode()

        return {
            "patients.csv": patients,
            "labels.csv": labels,
            "events.csv": events,
            "notes.csv": notes,
            "intake.csv": intake,
            "coverage.csv": coverage,
            "encounter_truth.csv": truth,
            "heroes.json": heroes,
        }
