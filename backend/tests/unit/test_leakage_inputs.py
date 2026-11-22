"""US-003-2: the pre-cutoff input set and the cohort leakage guardrail.

AC-027 (strictly-before-cutoff inputs, undated family history included),
AC-008 (no ground-truth key under any name), AC-028 (rendered reads exclude
post-cutoff items), AC-029 (the guardrail names the patient and the offending
event; zero violations is the only pass).
"""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest

from app.engine.inputs import GROUND_TRUTH_KEYS, ground_truth_keys_in, input_set, is_pre_cutoff
from app.guardrails import leakage
from app.labels import PatientLabel
from app.models import Event, Patient
from app.routers.data import _timeline_items

CUTOFF = date(2021, 1, 1)


def _patient(db, name: str = "Ada") -> Patient:
    patient = Patient(dataset_patient_id=f"P-{name}", dataset_version="v", display_name=name)
    db.add(patient)
    db.flush()
    return patient


def _label(db, patient: Patient, cutoff: date | None) -> None:
    db.add(
        PatientLabel(
            patient_id=patient.id,
            dataset_version="v",
            split="train",
            eval_cutoff_date=cutoff,
        )
    )


def _event(
    db, patient: Patient, *, when, event_type="encounter", display="x", event_id="E"
) -> None:
    db.add(
        Event(
            patient_id=patient.id,
            source_event_id=event_id,
            event_time=when,
            event_type=event_type,
            display=display,
            source_type="ehr",
            source_ref=f"ehr:{event_id}",
            dataset_version="v",
        )
    )


@pytest.fixture
def seeded(db_session):
    """A patient with a pre-cutoff item, an on-cutoff item, a post-cutoff
    diagnosis and workup, and one undated family-history row."""
    patient = _patient(db_session)
    _label(db_session, patient, CUTOFF)
    _event(db_session, patient, when=datetime(2019, 4, 2, 9, tzinfo=UTC), event_id="PRE")
    _event(
        db_session,
        patient,
        when=datetime(2021, 1, 1, 0, 0, tzinfo=UTC),
        event_id="ON",
        display="exactly on the cutoff",
    )
    _event(
        db_session,
        patient,
        when=datetime(2021, 1, 31, tzinfo=UTC),
        event_id="DIAG",
        event_type="condition",
        display="diagnosis confirmed at rheumatology",
    )
    _event(
        db_session,
        patient,
        when=datetime(2021, 1, 10, tzinfo=UTC),
        event_id="WORKUP",
        event_type="imaging",
        display="rheumatology workup sacroiliac imaging",
    )
    _event(
        db_session,
        patient,
        when=None,
        event_id="FAM",
        event_type="family_history",
        display="family history of axial disease",
    )
    db_session.commit()
    return patient


# ------------------------------------------------------- AC-027 the boundary


def test_ac027_an_item_dated_exactly_on_the_cutoff_is_excluded(db_session, seeded) -> None:
    items = input_set(db_session, seeded.id)["items"]

    ids = [item["event_id"] for item in items]
    assert "PRE" in ids
    assert "ON" not in ids


def test_ac027_the_undated_family_history_row_is_included(db_session, seeded) -> None:
    ids = [item["event_id"] for item in input_set(db_session, seeded.id)["items"]]

    assert "FAM" in ids


def test_ac027_the_boundary_helper_is_strictly_before_the_cutoff() -> None:
    assert is_pre_cutoff(datetime(2020, 12, 31, 23, 59, tzinfo=UTC), CUTOFF) is True
    assert is_pre_cutoff(datetime(2021, 1, 1, 0, 0, tzinfo=UTC), CUTOFF) is False
    assert is_pre_cutoff(None, CUTOFF, "family_history") is True
    assert is_pre_cutoff(None, CUTOFF, "encounter") is False


def test_ac027_a_patient_with_no_cutoff_keeps_todays_behaviour(db_session) -> None:
    patient = _patient(db_session, "NoCutoff")
    _label(db_session, patient, None)
    _event(db_session, patient, when=datetime(2099, 1, 1, tzinfo=UTC), event_id="FUTURE")
    db_session.commit()

    built = input_set(db_session, patient.id)

    assert built["has_cutoff"] is False
    assert [item["event_id"] for item in built["items"]] == ["FUTURE"]
    assert patient.id in leakage.unchecked_patients(db_session)


# -------------------------------------------------------- AC-008 ground truth


def test_ac008_no_input_set_carries_a_ground_truth_key_under_any_name(db_session, seeded) -> None:
    assert ground_truth_keys_in(input_set(db_session, seeded.id)) == []


def test_ac008_the_scan_finds_a_ground_truth_key_wherever_it_hides() -> None:
    payload = {"items": [{"meta": {"HLA_B27_true": True}}]}

    assert [key.lower() for key in ground_truth_keys_in(payload)] == ["hla_b27_true"]
    assert "archetype" in GROUND_TRUTH_KEYS


# ---------------------------------------------- AC-028 the rendered timelines


def test_ac028_a_confirmed_case_shows_neither_its_diagnosis_nor_its_workup(
    db_session, seeded
) -> None:
    displays = [item["display"] for item in _timeline_items(db_session, seeded)]

    assert "diagnosis confirmed at rheumatology" not in displays
    assert "rheumatology workup sacroiliac imaging" not in displays
    assert "family history of axial disease" in displays


# -------------------------------------------------------------- AC-029 sweep


def test_ac029_the_guardrail_passes_over_a_clean_cohort(db_session) -> None:
    patient = _patient(db_session, "Clean")
    _label(db_session, patient, CUTOFF)
    _event(db_session, patient, when=datetime(2019, 1, 1, tzinfo=UTC), event_id="OK")
    db_session.commit()

    result = leakage.check_cohort(db_session)

    assert result.ok is True
    assert result.count == 0


def test_ac029_the_whole_cohort_passes_once_the_filter_is_in_place(db_session, seeded) -> None:
    """The seeded patient has post-cutoff events in the store; none reach its
    input set, so the sweep over the loaded cohort is clean."""
    assert leakage.check_cohort(db_session).ok is True


def test_ac029_a_seeded_leaking_patient_yields_a_non_empty_violation_list(
    db_session, seeded, monkeypatch
) -> None:
    """With the cutoff filter bypassed, the sweep names the patient, the
    offending events and the ground-truth column."""
    leaking = {
        "patient_id": seeded.id,
        "items": [
            {
                "event_id": row.source_event_id,
                "event_time": row.event_time,
                "event_type": row.event_type,
            }
            for row in db_session.query(Event).filter(Event.patient_id == seeded.id)
        ],
        "archetype": "classic",
    }
    monkeypatch.setattr(leakage, "input_set", lambda db, patient_id: leaking)

    result = leakage.check_cohort(db_session)

    assert result.ok is False
    assert result.violations
    where = " ".join(violation.where for violation in result.violations)
    detail = " ".join(violation.detail for violation in result.violations)
    assert seeded.id in where
    assert "DIAG" in where and "WORKUP" in where and "ON" in where
    assert "2021-01-01" in detail
    assert "archetype" in detail
    assert all(violation.guardrail == leakage.GUARDRAIL for violation in result.violations)
