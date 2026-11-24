"""A dataset drop built for the tier guarantees (US-012: AC-033..AC-037, AC-039, AC-040).

Six patients, each one shaped for exactly one thing a criterion asks about:

* `short` and `mid`: reachable history well under the pack's
  `thresholds.reachable_history_months`, so both sit at "Insufficient history"
  while the shipped threshold (24 months) is in force. `mid` has twelve months
  of reachable history, so lowering the threshold to nine months must move it
  out of that set and leave `short` (six months) in it -- the set changes with
  no code change (AC-040).
* `full`: a long reachable history and a strong picture, so it is the control
  that is never at "Insufficient history".
* `postpartum`: the same strong picture plus an imaging report carrying
  iliac-side-only sclerosis, erosions explicitly absent, and symptom onset
  timed to the postpartum period (AC-033).
* `widespread`: widespread pain (a fibromyalgia-coded problem), a normal CRP
  result and an intake answer recording poor NSAID response (AC-034).
* `load`: an imaging report describing load-related sacroiliac bone-marrow
  oedema, and a note recording that the pain is worse with activity (AC-035).

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

#: Every cutoff is far in the future, so nothing in this drop is hidden by the
#: leakage guarantee and a missing item means a missing item.
CUTOFF = "2030-01-01"

#: Months of reachable history each fixture patient has, by role.
REACHABLE_MONTHS: dict[str, int] = {"short": 6, "mid": 12, "full": 240}

#: Reachable-history start dates giving those months against CUTOFF.
REACHABLE_START: dict[str, str] = {
    "short": "2029-07-01",
    "mid": "2029-01-01",
    "full": "2010-01-01",
}

#: The shipped pack's threshold, and the one AC-040 lowers it to. Nine months
#: sits strictly between `short` (6) and `mid` (12), so the set of patients at
#: "Insufficient history" must lose `mid` and keep `short`.
SHIPPED_THRESHOLD_MONTHS = 24
LOWERED_THRESHOLD_MONTHS = 9

#: The counter-evidence words each scenario's case read must carry, per AC.
#: Matched case-insensitively against the item's label and plain language.
AC033_WORDS = ("iliac", "erosion", "postpartum")
AC034_WORDS = ("widespread", "crp", "nsaid")
AC035_WORDS = ("load",)

TIERS = ("High", "Moderate", "Low", "Insufficient history")


def _csv(columns: tuple[str, ...], rows: list[dict[str, str]]) -> bytes:
    buffer = io.StringIO()
    writer = DictWriter(buffer, fieldnames=list(columns), lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({column: row.get(column, "") for column in columns})
    return buffer.getvalue().encode()


def _event(**values: str) -> dict[str, str]:
    return {column: values.get(column, "") for column in EVENT_COLUMNS}


class TierDrop:
    """One dataset drop whose tier inputs the test knows patient by patient."""

    def __init__(self, suffix: str) -> None:
        self.suffix = suffix
        self.dataset_version = f"qa-tiers-{suffix}"
        self.cutoff = CUTOFF

        self.short = f"TIERSHORT-{suffix}"
        self.mid = f"TIERMID-{suffix}"
        self.full = f"TIERFULL-{suffix}"
        self.postpartum = f"TIERPOST-{suffix}"
        self.widespread = f"TIERWIDE-{suffix}"
        self.load = f"TIERLOAD-{suffix}"
        self.patient_ids = (
            self.short,
            self.mid,
            self.full,
            self.postpartum,
            self.widespread,
            self.load,
        )

        #: Patients whose reachable history is under the shipped threshold.
        self.below_shipped_threshold = (self.short, self.mid)
        #: Patients still under the lowered threshold (nine months).
        self.below_lowered_threshold = (self.short,)

        self.imaging_source_ref = f"ehr:note:{suffix}:post-img"
        self.load_source_ref = f"ehr:note:{suffix}:load-img"
        self.load_pain_source_ref = f"ehr:note:{suffix}:load-clinic"
        self.widespread_source_ref = f"ehr:note:{suffix}:wide-clinic"

        self.postpartum_text = (
            "MRI of the sacroiliac joints was performed. "
            "Sclerosis is confined to the iliac side of the joint. "
            "No erosions are identified. "
            "Symptoms began three months postpartum after her second delivery."
        )
        self.load_imaging_text = (
            "MRI of the sacroiliac joints shows bone marrow oedema in a "
            "load-related distribution at the inferior joint margins. "
            "The appearances follow a load-related mechanical pattern."
        )
        self.load_pain_text = (
            "The pain is worse with activity and loading, and eases with rest. "
            "There is no night pain and no prolonged morning stiffness."
        )
        self.widespread_text = (
            "Reports widespread pain across all four quadrants with marked fatigue. "
            "CRP is normal. "
            "Anti-inflammatories gave no meaningful relief after a full trial."
        )

    # ----------------------------------------------------------- the patients

    def _patient_rows(self) -> list[dict[str, str]]:
        long_start = REACHABLE_START["full"]
        return [
            {
                "patient_id": self.short,
                "display_name": f"Tier Short {self.suffix}",
                "birth_year": "1988",
                "sex": "F",
                "reachable_history_start": REACHABLE_START["short"],
            },
            {
                "patient_id": self.mid,
                "display_name": f"Tier Mid {self.suffix}",
                "birth_year": "1986",
                "sex": "M",
                "reachable_history_start": REACHABLE_START["mid"],
            },
            {
                "patient_id": self.full,
                "display_name": f"Tier Full {self.suffix}",
                "birth_year": "1984",
                "sex": "F",
                "reachable_history_start": long_start,
            },
            {
                "patient_id": self.postpartum,
                "display_name": f"Tier Postpartum {self.suffix}",
                "birth_year": "1990",
                "sex": "F",
                "reachable_history_start": long_start,
            },
            {
                "patient_id": self.widespread,
                "display_name": f"Tier Widespread {self.suffix}",
                "birth_year": "1982",
                "sex": "F",
                "reachable_history_start": long_start,
            },
            {
                "patient_id": self.load,
                "display_name": f"Tier Load {self.suffix}",
                "birth_year": "1987",
                "sex": "M",
                "reachable_history_start": long_start,
            },
        ]

    # ------------------------------------------------------------- the events

    def _strong_picture(self, pid: str, tag: str) -> list[dict[str, str]]:
        """A picture that would reach the top tier on its own: chronic back
        pain recorded twice, sacroiliitis on imaging and a positive HLA-B27."""
        return [
            _event(
                patient_id=pid,
                event_id=f"BP1-{tag}-{self.suffix}",
                event_time="2019-02-02T09:00:00Z",
                event_type="encounter",
                code_system="ICD-10",
                code="M54.5",
                display=f"Back pain visit one {tag} {self.suffix}",
                provider_org="Clinic A",
                provider_specialty="primary_care",
                source_type="ehr",
                source_ref=f"ehr:enc:{self.suffix}:{tag}:1",
                encounter_ref=f"ENC-{tag}1-{self.suffix}",
                confidence="0.9",
            ),
            _event(
                patient_id=pid,
                event_id=f"BP2-{tag}-{self.suffix}",
                event_time="2019-08-02T09:00:00Z",
                event_type="encounter",
                code_system="ICD-10",
                code="M54.5",
                display=f"Back pain visit two {tag} {self.suffix}",
                provider_org="Clinic A",
                provider_specialty="primary_care",
                source_type="ehr",
                source_ref=f"ehr:enc:{self.suffix}:{tag}:2",
                encounter_ref=f"ENC-{tag}2-{self.suffix}",
                confidence="0.9",
            ),
            _event(
                patient_id=pid,
                event_id=f"SI-{tag}-{self.suffix}",
                event_time="2020-01-15T09:00:00Z",
                event_type="imaging",
                code_system="ICD-10",
                code="M46.1",
                display=f"Sacroiliitis reported on imaging {tag} {self.suffix}",
                provider_org="Imaging Centre",
                provider_specialty="radiology",
                source_type="ehr",
                source_ref=f"ehr:img:{self.suffix}:{tag}",
                encounter_ref=f"ENC-{tag}3-{self.suffix}",
                confidence="0.9",
            ),
            _event(
                patient_id=pid,
                event_id=f"B27-{tag}-{self.suffix}",
                event_time="2020-02-01T09:00:00Z",
                event_type="lab",
                code_system="LOINC",
                code="17695-9",
                display=f"Genetic marker test {tag} {self.suffix}",
                value="positive",
                provider_org="Clinic A",
                provider_specialty="primary_care",
                source_type="ehr",
                source_ref=f"ehr:lab:{self.suffix}:{tag}",
                encounter_ref=f"ENC-{tag}4-{self.suffix}",
                confidence="0.9",
            ),
        ]

    def _events(self) -> list[dict[str, str]]:
        rows: list[dict[str, str]] = []
        for pid, tag in (
            (self.full, "full"),
            (self.postpartum, "post"),
            (self.widespread, "wide"),
            (self.load, "load"),
        ):
            rows.extend(self._strong_picture(pid, tag))
        # The two short-history patients still have one visit each, so they are
        # loaded patients rather than empty rows.
        short_rows = ((self.short, "short", "2029-08-01"), (self.mid, "mid", "2029-03-01"))
        for pid, tag, when in short_rows:
            rows.append(
                _event(
                    patient_id=pid,
                    event_id=f"BP-{tag}-{self.suffix}",
                    event_time=f"{when}T09:00:00Z",
                    event_type="encounter",
                    code_system="ICD-10",
                    code="M54.5",
                    display=f"Back pain visit {tag} {self.suffix}",
                    provider_org="Clinic A",
                    provider_specialty="primary_care",
                    source_type="ehr",
                    source_ref=f"ehr:enc:{self.suffix}:{tag}",
                    encounter_ref=f"ENC-{tag}-{self.suffix}",
                    confidence="0.9",
                )
            )
        # AC-033: the imaging report whose wording carries all three clues.
        rows.append(
            _event(
                patient_id=self.postpartum,
                event_id=f"IMG-POST-{self.suffix}",
                event_time="2020-03-01T09:00:00Z",
                event_type="imaging",
                code_system="CPT",
                code="72195",
                display=f"MRI sacroiliac joints postpartum {self.suffix}",
                provider_org="Imaging Centre",
                provider_specialty="radiology",
                source_type="ehr",
                source_ref=self.imaging_source_ref,
                encounter_ref=f"ENC-POSTIMG-{self.suffix}",
                confidence="0.9",
            )
        )
        # AC-034: widespread pain coded, a normal CRP, and the clinic note.
        rows.extend(
            [
                _event(
                    patient_id=self.widespread,
                    event_id=f"FM-{self.suffix}",
                    event_time="2020-04-01T09:00:00Z",
                    event_type="condition",
                    code_system="ICD-10",
                    code="M79.7",
                    display=f"Widespread pain syndrome {self.suffix}",
                    provider_org="Clinic B",
                    provider_specialty="primary_care",
                    source_type="ehr",
                    source_ref=f"ehr:cond:{self.suffix}:fm",
                    encounter_ref=f"ENC-FM-{self.suffix}",
                    confidence="0.9",
                ),
                _event(
                    patient_id=self.widespread,
                    event_id=f"CRP-{self.suffix}",
                    event_time="2020-04-02T09:00:00Z",
                    event_type="lab",
                    code_system="LOINC",
                    code="1988-5",
                    display=f"Inflammatory marker {self.suffix}",
                    value="2",
                    unit="mg/L",
                    provider_org="Clinic B",
                    provider_specialty="primary_care",
                    source_type="ehr",
                    source_ref=f"ehr:lab:{self.suffix}:crp",
                    encounter_ref=f"ENC-CRP-{self.suffix}",
                    confidence="0.9",
                ),
                _event(
                    patient_id=self.widespread,
                    event_id=f"WIDE-NOTE-{self.suffix}",
                    event_time="2020-04-03T09:00:00Z",
                    event_type="note",
                    code_system="SNOMED",
                    code="11",
                    display=f"Clinic note widespread pain {self.suffix}",
                    provider_org="Clinic B",
                    provider_specialty="primary_care",
                    source_type="ehr",
                    source_ref=self.widespread_source_ref,
                    encounter_ref=f"ENC-WIDE-{self.suffix}",
                    confidence="0.9",
                ),
            ]
        )
        # AC-035: load-related bone-marrow oedema and activity-worsened pain.
        rows.extend(
            [
                _event(
                    patient_id=self.load,
                    event_id=f"IMG-LOAD-{self.suffix}",
                    event_time="2020-05-01T09:00:00Z",
                    event_type="imaging",
                    code_system="CPT",
                    code="72195",
                    display=f"MRI sacroiliac joints load pattern {self.suffix}",
                    provider_org="Imaging Centre",
                    provider_specialty="radiology",
                    source_type="ehr",
                    source_ref=self.load_source_ref,
                    encounter_ref=f"ENC-LOADIMG-{self.suffix}",
                    confidence="0.9",
                ),
                _event(
                    patient_id=self.load,
                    event_id=f"LOAD-NOTE-{self.suffix}",
                    event_time="2020-05-02T09:00:00Z",
                    event_type="note",
                    code_system="SNOMED",
                    code="12",
                    display=f"Clinic note activity worsened pain {self.suffix}",
                    provider_org="Clinic C",
                    provider_specialty="primary_care",
                    source_type="ehr",
                    source_ref=self.load_pain_source_ref,
                    encounter_ref=f"ENC-LOADN-{self.suffix}",
                    confidence="0.9",
                ),
            ]
        )
        return rows

    # -------------------------------------------------------------- the files

    def files(self) -> dict[str, bytes]:
        patients = _csv(
            ("patient_id", "display_name", "birth_year", "sex", "reachable_history_start"),
            self._patient_rows(),
        )
        splits = ("train", "val", "test", "train", "val", "test")
        labels = _csv(
            LABEL_COLUMNS,
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
                for pid, split in zip(self.patient_ids, splits, strict=True)
            ],
        )
        notes = _csv(
            ("patient_id", "source_ref", "note_time", "note_type", "text"),
            [
                {
                    "patient_id": self.postpartum,
                    "source_ref": self.imaging_source_ref,
                    "note_time": "2020-03-01T09:00:00Z",
                    "note_type": "imaging_report",
                    "text": self.postpartum_text,
                },
                {
                    "patient_id": self.load,
                    "source_ref": self.load_source_ref,
                    "note_time": "2020-05-01T09:00:00Z",
                    "note_type": "imaging_report",
                    "text": self.load_imaging_text,
                },
                {
                    "patient_id": self.load,
                    "source_ref": self.load_pain_source_ref,
                    "note_time": "2020-05-02T09:00:00Z",
                    "note_type": "clinic_note",
                    "text": self.load_pain_text,
                },
                {
                    "patient_id": self.widespread,
                    "source_ref": self.widespread_source_ref,
                    "note_time": "2020-04-03T09:00:00Z",
                    "note_type": "clinic_note",
                    "text": self.widespread_text,
                },
            ],
        )
        intake_rows = [
            {
                "patient_id": pid,
                "question_key": key,
                "answer_value": value,
                "answered_at": "2021-01-02T10:00:00Z",
                "is_complete": "true",
            }
            for pid, key, value in (
                (self.full, "age_at_onset", "29"),
                (self.full, "night_pain", "yes"),
                (self.full, "morning_stiffness", "yes"),
                (self.full, "better_with_movement", "yes"),
                (self.postpartum, "age_at_onset", "31"),
                (self.postpartum, "night_pain", "yes"),
                (self.postpartum, "morning_stiffness", "yes"),
                (self.widespread, "age_at_onset", "33"),
                (self.widespread, "nsaid_relief", "no"),
                (self.load, "age_at_onset", "30"),
                (self.load, "nsaid_relief", "no"),
            )
        ]
        intake = _csv(
            ("patient_id", "question_key", "answer_value", "answered_at", "is_complete"),
            intake_rows,
        )
        coverage = _csv(
            ("patient_id", "payer", "start_date", "end_date", "gap_reason"),
            [
                {
                    "patient_id": pid,
                    "payer": "Payer One",
                    "start_date": REACHABLE_START["full"],
                    "end_date": "2029-12-31",
                }
                for pid in (self.full, self.postpartum, self.widespread, self.load)
            ],
        )
        truth = _csv(
            ("patient_id", "true_encounter_id", "encounter_time", "visible_in_sources"),
            [
                {
                    "patient_id": pid,
                    "true_encounter_id": f"T-{index}-{self.suffix}",
                    "encounter_time": "2019-02-02T09:00:00Z",
                    "visible_in_sources": "true",
                }
                for index, pid in enumerate(self.patient_ids, start=1)
            ],
        )
        heroes = json.dumps(
            [
                {
                    "persona_key": f"tiers-{self.suffix}",
                    "name": f"Tier Full {self.suffix}",
                    "one_line_description": "Tier-guarantee fixture persona.",
                    "patient_id": self.full,
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
