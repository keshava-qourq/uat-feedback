"""US-012-2: counter-evidence rules inside the scoring engine (AC-033..AC-036).

Every rule key, cap target, plain-language sentence and alternative
explanation is read back from the active condition pack, never spelled out
here (NFR-019). The findings the imaging-wording rules read are produced by
the real clue extractor's pack-declared fallback, so there is one extraction
path only.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from typing import Any

import pytest
from sqlalchemy.orm import Session

from app import clue_extraction
from app.engine.counter_evidence import apply_cap, counter_evidence, tier_rank
from app.engine.criteria import pack_config
from app.engine.scoring import score_patient
from app.engine.tiers import TIER_HIGH, TIER_INSUFFICIENT_HISTORY, TIER_LOW, TIER_MODERATE
from app.labels import PatientLabel
from app.models import Event, IntakeAnswer, Note, Patient

CUTOFF = date(2030, 1, 1)
VERSION = "unit-counter"

POSTPARTUM_TEXT = (
    "MRI of the sacroiliac joints was performed. "
    "Sclerosis is confined to the iliac side of the joint. "
    "No erosions are identified. "
    "Symptoms began three months postpartum after her second delivery."
)
WIDESPREAD_TEXT = (
    "Reports widespread pain across all four quadrants with marked fatigue. "
    "CRP is normal. "
    "Anti-inflammatories gave no meaningful relief after a full trial."
)
LOAD_IMAGING_TEXT = (
    "MRI of the sacroiliac joints shows bone marrow oedema in a load-related "
    "distribution at the inferior joint margins. "
    "The appearances follow a load-related mechanical pattern."
)
LOAD_PAIN_TEXT = (
    "The pain is worse with activity and loading, and eases with rest. "
    "There is no night pain and no prolonged morning stiffness."
)


def _pack(db: Session) -> dict[str, Any]:
    config = pack_config(db)
    assert config is not None, "no condition pack is active, so nothing can be scored"
    return config


def _patient(db: Session, name: str) -> Patient:
    patient = Patient(
        dataset_patient_id=f"P-{name}-{uuid.uuid4().hex[:6]}",
        dataset_version=VERSION,
        display_name=name,
    )
    db.add(patient)
    db.flush()
    db.add(
        PatientLabel(
            patient_id=patient.id,
            dataset_version=VERSION,
            split="train",
            eval_cutoff_date=CUTOFF,
        )
    )
    db.commit()
    return patient


def _event(db: Session, patient: Patient, *, code: str, when: datetime, eid: str) -> None:
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
            dataset_version=VERSION,
        )
    )
    db.commit()


def _note(db: Session, patient: Patient, text: str) -> Note:
    note = Note(
        patient_id=patient.id,
        source_ref=f"ehr:note:{uuid.uuid4().hex[:8]}",
        note_time=datetime(2020, 5, 1, tzinfo=UTC),
        note_type="imaging_report",
        text=text,
    )
    db.add(note)
    db.commit()
    return note


def _extract(db: Session) -> None:
    """Run the real extractor with no model configured: the pack's wording."""
    clue_extraction.extract_cohort(db, client=None)


def _strong_picture(db: Session, patient: Patient) -> None:
    """Enough met criteria that the bands alone would put this patient on top."""
    config = _pack(db)
    signals = config["signals"]
    lists = config["code_lists"]
    # Chronic back pain twice, plus sacroiliac imaging: strong on the points.
    for key, count in ((k, int(v.get("min_occurrences") or 1)) for k, v in signals.items()):
        code_lists = signals[key].get("code_lists") or []
        if not code_lists or signals[key].get("positive_values"):
            continue
        code = str((lists[code_lists[0]].get("codes") or [""])[0])
        for index in range(count):
            _event(
                db,
                patient,
                code=code,
                when=datetime(2019, 2, 2, tzinfo=UTC),
                eid=f"{key}-{index}-{uuid.uuid4().hex[:6]}",
            )
    for signal in signals.values():
        for intake_key in signal.get("intake_keys") or []:
            db.add(
                IntakeAnswer(
                    patient_id=patient.id,
                    question_key=intake_key,
                    answer_value="yes",
                    answered_at=datetime(2021, 1, 2, tzinfo=UTC),
                    is_complete=True,
                )
            )
    db.commit()


def _keys(items: list[dict[str, Any]]) -> list[str]:
    return [item["key"] for item in items]


def _words(items: list[dict[str, Any]]) -> str:
    return " ".join(
        f"{item['key']} {item['label']} {item['plain_language']}" for item in items
    ).lower()


# -------------------------------------------------------------------- AC-033


def test_ac033_the_postpartum_case_is_capped_below_high_with_each_item_listed(
    db_session: Session,
) -> None:
    patient = _patient(db_session, "postpartum")
    _strong_picture(db_session, patient)
    _note(db_session, patient, POSTPARTUM_TEXT)
    _extract(db_session)

    result = score_patient(db_session, patient.id)
    items = result["counter_evidence"]

    assert tier_rank(result["tier"]) < tier_rank(TIER_HIGH), result["tier"]
    words = _words(items)
    for word in ("iliac", "erosion", "postpartum"):
        assert word in words, f"{word} is in no listed item: {_keys(items)}"
    assert len(set(_keys(items))) == len(items), _keys(items)
    assert len(items) >= 3, _keys(items)


def test_ac033_the_postpartum_case_names_the_alternative_explanation_from_the_pack(
    db_session: Session,
) -> None:
    config = _pack(db_session)
    patient = _patient(db_session, "alternative")
    _strong_picture(db_session, patient)
    _note(db_session, patient, POSTPARTUM_TEXT)
    _extract(db_session)

    alternative = score_patient(db_session, patient.id)["alternative_explanation"]

    assert isinstance(alternative, dict)
    declared = {
        str(rule.get("alternative_explanation"))
        for rule in config["counter_evidence"].values()
        if rule.get("alternative_explanation")
    }
    assert alternative["label"] in declared


# -------------------------------------------------------------------- AC-034


def test_ac034_the_widespread_pain_case_is_capped_no_higher_than_moderate(
    db_session: Session,
) -> None:
    patient = _patient(db_session, "widespread")
    _strong_picture(db_session, patient)
    _note(db_session, patient, WIDESPREAD_TEXT)
    _extract(db_session)

    result = score_patient(db_session, patient.id)
    items = result["counter_evidence"]

    assert tier_rank(result["tier"]) <= tier_rank(TIER_MODERATE), result["tier"]
    words = _words(items)
    for word in ("widespread", "crp", "nsaid"):
        assert word in words, f"{word} is in no listed item: {_keys(items)}"
    caps = [item for item in items if item["effect"] == "cap"]
    assert caps, _keys(items)
    assert all(item["capped_to"] for item in caps)


# -------------------------------------------------------------------- AC-035


def test_ac035_the_load_related_pattern_is_recorded_and_caps_below_high(
    db_session: Session,
) -> None:
    patient = _patient(db_session, "load")
    _strong_picture(db_session, patient)
    _note(db_session, patient, LOAD_IMAGING_TEXT)
    _note(db_session, patient, LOAD_PAIN_TEXT)
    _extract(db_session)

    result = score_patient(db_session, patient.id)

    assert "load" in _words(result["counter_evidence"])
    assert tier_rank(result["tier"]) < tier_rank(TIER_HIGH), result["tier"]


# -------------------------------------------------------------------- AC-036


def test_ac036_every_fired_rule_states_its_sentence_cap_evidence_and_marker(
    db_session: Session,
) -> None:
    config = _pack(db_session)
    patient = _patient(db_session, "fired")
    _strong_picture(db_session, patient)
    _note(db_session, patient, POSTPARTUM_TEXT)
    _extract(db_session)

    items = counter_evidence(db_session, patient.id)["items"]

    assert items
    for item in items:
        rule = config["counter_evidence"][item["key"]]
        assert item["plain_language"] == rule["plain_language"]
        assert len(item["plain_language"].split()) >= 3
        assert item["capped_to"] in {TIER_HIGH, TIER_MODERATE, TIER_LOW}
        assert item["awaiting_sign_off"] is bool(rule.get("requires_sign_off"))
        assert item["evidence"]
        for entry in item["evidence"]:
            for field in ("display", "date", "source_tag", "source_ref"):
                assert str(entry.get(field) or "").strip(), (item["key"], field)
            assert entry["note_link"].endswith(entry["source_ref"])


def test_ac036_a_rule_the_pack_does_not_mark_returns_awaiting_sign_off_false(
    db_session: Session,
) -> None:
    config = _pack(db_session)
    patient = _patient(db_session, "signoff")
    _strong_picture(db_session, patient)
    _note(db_session, patient, WIDESPREAD_TEXT)
    _extract(db_session)

    items = counter_evidence(db_session, patient.id)["items"]
    unmarked = [
        item
        for item in items
        if not config["counter_evidence"][item["key"]].get("requires_sign_off")
    ]

    assert unmarked, _keys(items)
    assert all(item["awaiting_sign_off"] is False for item in unmarked)


# ------------------------------------------------- a cap never raises a tier


@pytest.mark.parametrize(
    ("tier", "cap", "expected"),
    [
        (TIER_LOW, TIER_HIGH, TIER_LOW),
        (TIER_LOW, TIER_MODERATE, TIER_LOW),
        (TIER_HIGH, TIER_MODERATE, TIER_MODERATE),
        (TIER_HIGH, None, TIER_HIGH),
        (TIER_INSUFFICIENT_HISTORY, TIER_LOW, TIER_INSUFFICIENT_HISTORY),
        (TIER_INSUFFICIENT_HISTORY, TIER_HIGH, TIER_INSUFFICIENT_HISTORY),
    ],
)
def test_a_cap_only_ever_lowers_a_tier_and_never_overrides_insufficient_history(
    tier: str, cap: str | None, expected: str
) -> None:
    assert apply_cap(tier, cap) == expected


def test_a_capped_patient_with_a_short_history_stays_at_insufficient_history(
    db_session: Session,
) -> None:
    patient = _patient(db_session, "shorthistory")
    _note(db_session, patient, POSTPARTUM_TEXT)
    _event(
        db_session,
        patient,
        code="ZZZ-not-in-any-code-list",
        when=datetime(2029, 8, 1, tzinfo=UTC),
        eid=f"short-{uuid.uuid4().hex[:6]}",
    )
    _extract(db_session)

    result = score_patient(db_session, patient.id)

    assert result["tier"] == TIER_INSUFFICIENT_HISTORY
    assert result["counter_evidence"], "the fired rules are still listed"


# ------------------------------------------------------- nothing to report


def test_a_patient_with_no_counter_evidence_returns_an_empty_list(
    db_session: Session,
) -> None:
    patient = _patient(db_session, "clean")
    _strong_picture(db_session, patient)
    _note(db_session, patient, "Attended for a routine medication review. Nothing new.")
    _extract(db_session)

    result = score_patient(db_session, patient.id)

    assert result["counter_evidence"] == []
    assert result["alternative_explanation"] is None
    assert counter_evidence(db_session, patient.id)["cap"] is None
