"""US-012-1: the tier engine (AC-037, AC-038, AC-040).

Every threshold, code and point value in these assertions is read back from
the active condition pack, never spelled out here (NFR-019).
"""

from __future__ import annotations

import copy
from datetime import UTC, date, datetime
from typing import Any

import pytest

from app.engine.criteria import pack_config
from app.engine.scoring import REACHABLE_HISTORY_MONTHS, score_patient
from app.engine.tiers import (
    TIER_HIGH,
    TIER_INSUFFICIENT_HISTORY,
    TIER_LOW,
    TIER_MODERATE,
    TIERS,
)
from app.labels import PatientLabel
from app.models import ConditionPack, Event, Patient

CUTOFF = date(2022, 1, 1)
#: A date giving a long reachable history against the cutoff.
LONG_AGO = datetime(2015, 1, 1, tzinfo=UTC)


def _patient(db, name: str, *, earliest: datetime = LONG_AGO) -> Patient:
    patient = Patient(dataset_patient_id=f"P-{name}", dataset_version="v", display_name=name)
    db.add(patient)
    db.flush()
    db.add(
        PatientLabel(
            patient_id=patient.id,
            dataset_version="v",
            split="train",
            eval_cutoff_date=CUTOFF,
        )
    )
    # An item the pack's code lists do not name, fixing the reachable history.
    _event(db, patient, code="ZZZ-not-in-any-code-list", when=earliest, eid=f"{name}-base")
    db.commit()
    return patient


def _event(db, patient, *, code, when, eid):
    db.add(
        Event(
            patient_id=patient.id,
            source_event_id=eid,
            event_time=when,
            event_type="observation",
            code=code,
            display="A recorded finding",
            source_type="ehr",
            source_ref=f"ehr:{eid}",
            dataset_version="v",
        )
    )
    db.commit()


def _pack(db) -> dict[str, Any]:
    config = pack_config(db)
    assert config is not None, "no condition pack is active, so nothing can be scored"
    return config


def _points_criterion(config) -> dict[str, Any]:
    for item in (config.get("criteria") or {}).values():
        if (item or {}).get("kind") == "points":
            return item
    pytest.fail("the pack declares no points criterion")


def _candidates(config) -> list[tuple[int, str]]:
    """(points, code) for every point item answerable by one coded event."""
    points = _points_criterion(config)["items"]
    found: list[tuple[int, str]] = []
    for key, value in points.items():
        signal = (config.get("signals") or {}).get(key) or {}
        if signal.get("positive_values") or int(signal.get("min_occurrences") or 1) != 1:
            continue
        lists = signal.get("code_lists") or []
        if not lists:
            continue
        codes = (config["code_lists"][lists[0]] or {}).get("codes") or []
        if codes:
            found.append((int(value), str(codes[0])))
    return sorted(found)


def _code_for_strength(config, low: float, high: float | None) -> str:
    """A single code whose points put the evaluation in [low, high) of the
    points threshold the pack declares."""
    threshold = float(_points_criterion(config)["pass_score"])
    for points, code in _candidates(config):
        strength = min(points / threshold, 1.0)
        if strength >= low and (high is None or strength < high):
            return code
    pytest.fail(f"the pack offers no single coded item scoring in [{low}, {high})")


def _band_cut(config, tier: str) -> float:
    return float(config["thresholds"][tier.lower()])


def _scored(db, patient) -> dict[str, Any]:
    return score_patient(db, patient.id)


# ------------------------------------------------------------- the four tiers


def test_ac037_a_strong_case_scores_the_top_tier_as_a_word(db_session) -> None:
    config = _pack(db_session)
    patient = _patient(db_session, "high")
    _event(
        db_session,
        patient,
        code=_code_for_strength(config, _band_cut(config, TIER_HIGH), None),
        when=datetime(2021, 5, 1, tzinfo=UTC),
        eid="E-high",
    )

    result = _scored(db_session, patient)

    assert result["tier"] == TIER_HIGH
    assert result["tier"] in TIERS
    assert not isinstance(result["tier"], (int, float))


def test_ac037_a_middling_case_scores_the_middle_tier(db_session) -> None:
    config = _pack(db_session)
    patient = _patient(db_session, "moderate")
    _event(
        db_session,
        patient,
        code=_code_for_strength(
            config, _band_cut(config, TIER_MODERATE), _band_cut(config, TIER_HIGH)
        ),
        when=datetime(2021, 5, 1, tzinfo=UTC),
        eid="E-mod",
    )

    assert _scored(db_session, patient)["tier"] == TIER_MODERATE


def test_ac037_a_weak_case_with_a_long_history_scores_the_bottom_tier(db_session) -> None:
    config = _pack(db_session)
    patient = _patient(db_session, "low")
    _event(
        db_session,
        patient,
        code=_code_for_strength(config, 0.0, _band_cut(config, TIER_MODERATE)),
        when=datetime(2021, 5, 1, tzinfo=UTC),
        eid="E-low",
    )

    assert _scored(db_session, patient)["tier"] == TIER_LOW


def test_ac038_a_short_history_scores_insufficient_history(db_session) -> None:
    _pack(db_session)
    patient = _patient(db_session, "short", earliest=datetime(2021, 7, 1, tzinfo=UTC))

    result = _scored(db_session, patient)

    assert result["tier"] == TIER_INSUFFICIENT_HISTORY
    assert result["reachable_history"]["below_threshold"] is True


def test_ac037_the_headline_status_is_never_a_number(db_session) -> None:
    config = _pack(db_session)
    patient = _patient(db_session, "headline")
    _event(
        db_session,
        patient,
        code=_code_for_strength(config, _band_cut(config, TIER_HIGH), None),
        when=datetime(2021, 5, 1, tzinfo=UTC),
        eid="E-h2",
    )

    result = _scored(db_session, patient)

    assert isinstance(result["tier"], str)
    assert result["tier"].strip() in TIERS
    for key in ("score", "probability", "percentage", "risk_score"):
        assert key not in result


# ------------------------------------------------- AC-038 the gate wins over Low


def test_ac038_the_gate_wins_over_a_would_be_low(db_session) -> None:
    config = _pack(db_session)
    weak_code = _code_for_strength(config, 0.0, _band_cut(config, TIER_MODERATE))

    long_history = _patient(db_session, "long")
    _event(db_session, long_history, code=weak_code, when=LONG_AGO, eid="E-long")
    short_history = _patient(db_session, "brief", earliest=datetime(2021, 7, 1, tzinfo=UTC))
    _event(
        db_session,
        short_history,
        code=weak_code,
        when=datetime(2021, 8, 1, tzinfo=UTC),
        eid="E-brief",
    )

    assert _scored(db_session, long_history)["tier"] == TIER_LOW
    assert _scored(db_session, short_history)["tier"] == TIER_INSUFFICIENT_HISTORY


# ------------------------------------------- AC-040 the threshold comes from the pack


def _store_pack(db, config: dict[str, Any], version: int) -> None:
    db.add(ConditionPack(pack_key="scored", version=version, enabled=True, config=config))
    db.commit()


def test_ac040_the_result_states_months_threshold_and_below_threshold(db_session) -> None:
    config = _pack(db_session)
    patient = _patient(db_session, "stated", earliest=datetime(2021, 7, 1, tzinfo=UTC))

    history = _scored(db_session, patient)["reachable_history"]

    assert history["months"] == 6
    assert history["threshold_months"] == int(config["thresholds"][REACHABLE_HISTORY_MONTHS])
    assert history["below_threshold"] is True


def test_ac040_the_same_cohort_rescored_under_two_thresholds_differs(db_session) -> None:
    config = _pack(db_session)
    cohort = {
        "short": _patient(db_session, "c-short", earliest=datetime(2021, 7, 1, tzinfo=UTC)),
        "mid": _patient(db_session, "c-mid", earliest=datetime(2021, 1, 1, tzinfo=UTC)),
        "full": _patient(db_session, "c-full"),
    }

    def insufficient() -> set[str]:
        return {
            name
            for name, patient in cohort.items()
            if score_patient(db_session, patient.id)["tier"] == TIER_INSUFFICIENT_HISTORY
        }

    strict = copy.deepcopy(config)
    strict["thresholds"][REACHABLE_HISTORY_MONTHS] = 24
    _store_pack(db_session, strict, 1)
    assert insufficient() == {"short", "mid"}

    lenient = copy.deepcopy(config)
    lenient["thresholds"][REACHABLE_HISTORY_MONTHS] = 9
    _store_pack(db_session, lenient, 2)
    assert insufficient() == {"short"}
