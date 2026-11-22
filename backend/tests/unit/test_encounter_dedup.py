"""US-004-1: merging the EHR row and the claim that describe one visit."""

from __future__ import annotations

from datetime import UTC, datetime

from app.dedup import assign_groups, merge_items, visit_count
from app.models import Event, Patient
from app.routers.data import _timeline_items

WHEN = datetime(2019, 3, 4, 9, 0, tzinfo=UTC)


def _patient(db, name: str = "Ada") -> Patient:
    patient = Patient(dataset_patient_id=f"DS-{name}", dataset_version="v1", display_name=name)
    db.add(patient)
    db.flush()
    return patient


def _event(db, patient, *, event_id, source_type, when=WHEN, code="M54.5", ref=None, org="Clinic"):
    row = Event(
        patient_id=patient.id,
        source_event_id=event_id,
        event_time=when,
        event_type="encounter",
        code=code,
        display=f"{source_type} {event_id}",
        provider_org=org,
        source_type=source_type,
        source_ref=f"{source_type}:{event_id}",
        encounter_ref=ref,
        dataset_version="v1",
    )
    db.add(row)
    db.flush()
    return row


def test_ac011_two_source_rows_of_one_encounter_become_one_entry(db_session) -> None:
    patient = _patient(db_session)
    _event(db_session, patient, event_id="E1", source_type="ehr", ref="Encounter/ENC-1")
    _event(db_session, patient, event_id="C1", source_type="claim", ref="claim:ENC-1")
    db_session.commit()

    items = _timeline_items(db_session, patient)

    assert len(items) == 1
    assert items[0]["sources"] == ["ehr", "claim"]
    assert sorted(items[0]["merged_from"]) == ["C1", "E1"]
    assert items[0]["visit_count_contribution"] == 1


def test_ac011_a_near_in_time_claim_with_the_same_code_merges(db_session) -> None:
    patient = _patient(db_session, "Grace")
    _event(db_session, patient, event_id="E1", source_type="ehr")
    _event(
        db_session,
        patient,
        event_id="C1",
        source_type="claim",
        when=datetime(2019, 3, 4, 21, 0, tzinfo=UTC),
        org=None,
    )
    db_session.commit()

    items = _timeline_items(db_session, patient)

    assert len(items) == 1
    assert set(items[0]["sources"]) == {"ehr", "claim"}


def test_ac011_two_genuinely_separate_visits_stay_two_entries(db_session) -> None:
    patient = _patient(db_session, "Hedy")
    _event(db_session, patient, event_id="E1", source_type="ehr")
    _event(
        db_session,
        patient,
        event_id="C2",
        source_type="claim",
        when=datetime(2019, 8, 1, 9, 0, tzinfo=UTC),
        code="M45",
    )
    db_session.commit()

    items = _timeline_items(db_session, patient)

    assert len(items) == 2
    assert [item["sources"] for item in items] == [["ehr"], ["claim"]]
    assert [item["item_time"] for item in items] == sorted(item["item_time"] for item in items)


def test_ac011_two_ehr_rows_are_never_merged_with_each_other(db_session) -> None:
    patient = _patient(db_session, "Iris")
    _event(db_session, patient, event_id="E1", source_type="ehr")
    _event(db_session, patient, event_id="E2", source_type="ehr")
    db_session.commit()

    assert len(_timeline_items(db_session, patient)) == 2


def test_ac011_a_merged_encounter_counts_as_one_visit(db_session) -> None:
    patient = _patient(db_session, "Jean")
    _event(db_session, patient, event_id="E1", source_type="ehr", ref="Encounter/ENC-1")
    _event(db_session, patient, event_id="C1", source_type="claim", ref="ENC-1")
    _event(
        db_session,
        patient,
        event_id="E2",
        source_type="ehr",
        when=datetime(2020, 1, 5, 8, 0, tzinfo=UTC),
    )
    db_session.commit()

    items = _timeline_items(db_session, patient)

    assert visit_count(items) == 2


def test_ac011_the_merge_is_safe_to_run_twice(db_session) -> None:
    patient = _patient(db_session, "Katherine")
    _event(db_session, patient, event_id="E1", source_type="ehr", ref="Encounter/ENC-1")
    _event(db_session, patient, event_id="C1", source_type="claim", ref="ENC-1")
    db_session.commit()

    first = assign_groups(db_session)
    keys_after_first = sorted(row.encounter_group_id for row in db_session.query(Event))
    second = assign_groups(db_session)
    keys_after_second = sorted(row.encounter_group_id for row in db_session.query(Event))

    assert first == second == 1
    assert keys_after_first == keys_after_second
    assert len(set(keys_after_second)) == 1
    assert len(_timeline_items(db_session, patient)) == 1


def test_ac011_grouping_keys_are_server_generated_uuids(db_session) -> None:
    patient = _patient(db_session, "Lise")
    _event(db_session, patient, event_id="E1", source_type="ehr")
    db_session.commit()

    assign_groups(db_session)

    key = db_session.query(Event).one().encounter_group_id
    assert key and len(key) == 36


def test_ac011_merge_items_never_invents_an_entry_without_a_source_row() -> None:
    assert merge_items([]) == []
