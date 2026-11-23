"""US-010-1: the criteria evaluator behind GET /api/cases/{patient_id}.

Every name, point value and threshold in these assertions is read back from
the active condition pack, never spelled out here (NFR-019).
"""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest
from fastapi import HTTPException

from app.engine.criteria import (
    STATUS_MET,
    STATUS_NOT_MET,
    STATUS_UNKNOWN,
    evaluate_case,
    pack_config,
)
from app.labels import PatientLabel
from app.models import Event, IntakeAnswer, Patient, User
from app.routers.data import case_read

CUTOFF = date(2022, 1, 1)


def _patient(db, name: str = "Ada") -> Patient:
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
    db.commit()
    return patient


def _staff(db) -> User:
    user = User(email=f"c{datetime.now(UTC).timestamp()}@example.test", role="clinician")
    db.add(user)
    db.flush()
    return user


def _event(db, patient, *, code, value=None, when=datetime(2021, 5, 1, tzinfo=UTC), eid="E1"):
    db.add(
        Event(
            patient_id=patient.id,
            source_event_id=eid,
            event_time=when,
            event_type="observation",
            code=code,
            display="A recorded finding",
            value=value,
            source_type="ehr",
            source_ref=f"ehr:{eid}",
            dataset_version="v",
        )
    )
    db.commit()


def _answer(db, patient, key, value, when=datetime(2021, 6, 1, tzinfo=UTC)):
    db.add(
        IntakeAnswer(
            patient_id=patient.id,
            question_key=key,
            answer_value=value,
            answered_at=when,
            is_complete=False,
        )
    )
    db.commit()


def _pack(db):
    config = pack_config(db)
    assert config is not None, "no condition pack is active, so there is nothing to evaluate"
    return config


def _points_criterion(config):
    for key, item in (config.get("criteria") or {}).items():
        if (item or {}).get("kind") == "points":
            return key, item
    pytest.fail("the pack declares no points criterion")


def _signal_with_codes(config, *, with_values: bool):
    """A signal key whose code list is usable in a test, and its first code."""
    for key, signal in (config.get("signals") or {}).items():
        lists = signal.get("code_lists") or []
        has_values = bool(signal.get("positive_values"))
        if lists and has_values is with_values and int(signal.get("min_occurrences") or 1) == 1:
            codes = config["code_lists"][lists[0]].get("codes") or []
            if codes:
                return key, str(codes[0]), signal
    pytest.fail("the pack declares no usable code-list signal")


def _spartan(payload, config):
    key, _ = _points_criterion(config)
    section = payload["criteria"][key.split("_", 1)[0]]
    return section


def test_ac030_every_criterion_and_point_item_is_listed_with_a_status(db_session) -> None:
    config = _pack(db_session)
    patient = _patient(db_session)

    payload = evaluate_case(db_session, patient.id)

    set_keys = [
        key for key, item in config["criteria"].items() if (item or {}).get("kind") == "set"
    ]
    points_key, points = _points_criterion(config)
    listed = payload["criteria"][set_keys[0].split("_", 1)[0] + "_referral"]
    assert [row["key"] for row in listed] == set_keys
    section = payload["criteria"][points_key.split("_", 1)[0]]
    assert [row["key"] for row in section["items"]] == list(points["items"])
    assert section["threshold"] == points["pass_score"]
    for row in [*listed, *section["items"]]:
        assert row["status"] in {STATUS_MET, STATUS_NOT_MET, STATUS_UNKNOWN}


def test_ac031_a_met_point_item_carries_its_evidence_with_date_and_source_tag(db_session) -> None:
    config = _pack(db_session)
    signal_key, code, _ = _signal_with_codes(config, with_values=False)
    patient = _patient(db_session)
    _event(db_session, patient, code=code, eid="EV-7")

    section = _spartan(evaluate_case(db_session, patient.id), config)
    item = next((row for row in section["items"] if row["key"] == signal_key), None)
    if item is None:
        pytest.skip("that signal is not one of the pack's point items")

    assert item["status"] == STATUS_MET
    assert item["evidence"] == {
        "event_id": "EV-7",
        "display": "A recorded finding",
        "date": "2021-05-01",
        "source_tag": "ehr",
    }
    assert item["needed"] is None


def test_ac031_a_met_item_from_an_intake_answer_names_the_answer(db_session) -> None:
    config = _pack(db_session)
    _, points = _points_criterion(config)
    signal_key, signal = next(
        (key, value)
        for key, value in config["signals"].items()
        if value.get("intake_keys") and not value.get("code_lists") and key in points["items"]
    )
    patient = _patient(db_session)
    _answer(db_session, patient, signal["intake_keys"][0], "yes")

    section = _spartan(evaluate_case(db_session, patient.id), config)
    item = next(row for row in section["items"] if row["key"] == signal_key)

    assert item["status"] == STATUS_MET
    assert item["evidence"]["source_tag"] == "patient"
    assert item["evidence"]["date"] == "2021-06-01"
    assert signal["intake_keys"][0] in item["evidence"]["display"]


def test_ac031_an_answer_spelled_out_more_fully_than_the_pack_key_still_counts(
    db_session,
) -> None:
    config = _pack(db_session)
    _, points = _points_criterion(config)
    signal_key, signal = next(
        (key, value)
        for key, value in config["signals"].items()
        if value.get("intake_keys") and not value.get("code_lists") and key in points["items"]
    )
    patient = _patient(db_session)
    _answer(db_session, patient, f"{signal['intake_keys'][0]}_minutes", "75")

    section = _spartan(evaluate_case(db_session, patient.id), config)
    item = next(row for row in section["items"] if row["key"] == signal_key)

    assert item["status"] == STATUS_MET
    assert item["evidence"]["source_tag"] == "patient"


def test_ac032_an_item_nothing_can_answer_is_unknown_with_a_needed_string(db_session) -> None:
    config = _pack(db_session)
    signal_key, _, _ = _signal_with_codes(config, with_values=True)
    patient = _patient(db_session)

    section = _spartan(evaluate_case(db_session, patient.id), config)
    item = next(row for row in section["items"] if row["key"] == signal_key)

    assert item["status"] == STATUS_UNKNOWN
    assert item["evidence"] is None
    assert item["needed"]


def test_ac030_a_recorded_negative_result_is_not_met_not_unknown(db_session) -> None:
    config = _pack(db_session)
    signal_key, code, _ = _signal_with_codes(config, with_values=True)
    patient = _patient(db_session)
    _event(db_session, patient, code=code, value="negative", eid="EV-9")

    section = _spartan(evaluate_case(db_session, patient.id), config)
    item = next(row for row in section["items"] if row["key"] == signal_key)

    assert item["status"] == STATUS_NOT_MET
    assert item["needed"] is None


def test_ac032_unknown_items_are_never_added_into_the_total(db_session) -> None:
    config = _pack(db_session)
    signal_key, code, _ = _signal_with_codes(config, with_values=False)
    patient = _patient(db_session)
    _event(db_session, patient, code=code, eid="EV-3")

    section = _spartan(evaluate_case(db_session, patient.id), config)
    met_points = sum(row["points"] for row in section["items"] if row["status"] == STATUS_MET)
    unknown_points = sum(
        row["points"] for row in section["items"] if row["status"] == STATUS_UNKNOWN
    )

    assert unknown_points > 0, "this fixture is meant to leave some items unanswered"
    assert section["total"] == met_points
    assert section["total"] < met_points + unknown_points
    assert any(row["key"] == signal_key and row["status"] == STATUS_MET for row in section["items"])


def test_ac030_the_total_is_reported_against_the_packs_threshold(db_session) -> None:
    config = _pack(db_session)
    _, points = _points_criterion(config)
    patient = _patient(db_session)

    section = _spartan(evaluate_case(db_session, patient.id), config)

    assert section["threshold"] == points["pass_score"]
    assert section["total"] == 0


def test_ac030_an_event_on_or_after_the_cutoff_is_never_evidence(db_session) -> None:
    config = _pack(db_session)
    signal_key, code, _ = _signal_with_codes(config, with_values=False)
    patient = _patient(db_session)
    _event(
        db_session,
        patient,
        code=code,
        when=datetime(CUTOFF.year, CUTOFF.month, CUTOFF.day, tzinfo=UTC),
        eid="EV-LATE",
    )

    payload = evaluate_case(db_session, patient.id)
    section = _spartan(payload, config)
    item = next(row for row in section["items"] if row["key"] == signal_key)

    assert item["status"] != STATUS_MET
    assert "EV-LATE" not in str(payload)


def test_ac030_the_case_read_carries_the_notice_and_the_cutoff(db_session) -> None:
    patient = _patient(db_session)

    payload = case_read(patient.id, _staff(db_session), db_session)

    assert payload["notice"]
    assert payload["cutoff_date"] == CUTOFF.isoformat()
    assert payload["patient_id"] == patient.id


def test_ac030_an_unknown_patient_id_is_404(db_session) -> None:
    with pytest.raises(HTTPException) as raised:
        case_read("no-such-patient", _staff(db_session), db_session)

    assert raised.value.status_code == 404
