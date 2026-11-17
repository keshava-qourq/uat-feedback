"""US-002-1: provenance as a validated property of every stored event.

The row builder and the lookup are exercised directly: both are pure of the
queue and of RQ, so the acceptance criteria are proved without a worker.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.ingest import job as ingest_job
from app.models import Event, IngestFileResult, IngestRun, Note, Patient
from app.provenance import resolve_source_ref
from app.routers.data import _timeline_items
from app.routers.ingest_runs import _report

IDS = {"P1": "internal-uuid-1"}

FULL_ROW = {
    "patient_id": "P1",
    "event_id": "E1",
    "event_time": "2018-04-02T09:00:00Z",
    "event_type": "encounter",
    "code_system": "SNOMED",
    "code": "1",
    "display": "Visit",
    "value": "12",
    "unit": "mg/L",
    "provider_org": "Clinic A",
    "provider_specialty": "primary_care",
    "source_type": "ehr",
    "source_ref": "ehr:note:1",
    "encounter_ref": "ENC1",
    "confidence": "0.9",
}


def test_ac005_every_supplied_source_field_is_carried_onto_the_stored_row():
    built = ingest_job._event_row(dict(FULL_ROW), "v-test", IDS)

    assert built["patient_id"] == "internal-uuid-1"
    assert built["source_event_id"] == "E1"
    assert built["event_time"] == datetime(2018, 4, 2, 9, 0, tzinfo=UTC)
    assert built["event_type"] == "encounter"
    assert built["code_system"] == "SNOMED"
    assert built["code"] == "1"
    assert built["display"] == "Visit"
    assert built["value"] == "12"
    assert built["unit"] == "mg/L"
    assert built["provider_org"] == "Clinic A"
    assert built["provider_specialty"] == "primary_care"
    assert built["source_type"] == "ehr"
    assert built["source_ref"] == "ehr:note:1"
    assert built["encounter_ref"] == "ENC1"
    assert built["confidence"] == pytest.approx(0.9)


@pytest.mark.parametrize("source_type", ["ehr", "claim", "patient"])
def test_ac005_the_three_source_types_are_accepted(source_type):
    built = ingest_job._event_row({**FULL_ROW, "source_type": source_type}, "v", IDS)
    assert built["source_type"] == source_type


def test_ac005_any_other_source_type_is_rejected_as_a_provenance_failure():
    with pytest.raises(ingest_job._ProvenanceFailure) as exc:
        ingest_job._event_row({**FULL_ROW, "source_type": "fax"}, "v", IDS)
    assert "E1" in str(exc.value)
    assert "source_type" in str(exc.value)


@pytest.mark.parametrize("missing", ["source_type", "source_ref"])
def test_ac007_a_row_missing_a_provenance_field_names_the_event_and_the_field(missing):
    with pytest.raises(ingest_job._ProvenanceFailure) as exc:
        ingest_job._event_row({**FULL_ROW, missing: ""}, "v", IDS)
    assert "E1" in str(exc.value)
    assert missing in str(exc.value)


def _seed(db_session):
    patient = Patient(dataset_patient_id="P1", dataset_version="v", display_name="Ada")
    db_session.add(patient)
    db_session.flush()
    db_session.add(
        Note(
            patient_id=patient.id,
            source_ref="ehr:note:1",
            note_time=datetime(2018, 4, 2, 9, 30, tzinfo=UTC),
            note_type="clinic_note",
            text="Reports morning stiffness.",
        )
    )
    db_session.add(
        Event(
            patient_id=patient.id,
            source_event_id="E1",
            event_time=datetime(2018, 4, 2, 9, 0, tzinfo=UTC),
            event_type="encounter",
            source_type="ehr",
            source_ref="ehr:note:1",
            dataset_version="v",
        )
    )
    db_session.commit()
    return patient


def test_ac006_a_stored_events_source_ref_resolves_to_its_note(db_session):
    patient = _seed(db_session)
    event = db_session.query(Event).one()

    found = resolve_source_ref(db_session, event.source_ref, patient.id)

    assert found.found is True
    assert found.note_text == "Reports morning stiffness."
    assert found.note_type == "clinic_note"
    # SQLite, which this unit run uses, hands a timestamptz back without its
    # zone; the instant stored is the UTC one the row was written with.
    assert found.note_time.replace(tzinfo=UTC) == datetime(2018, 4, 2, 9, 30, tzinfo=UTC)


def test_ac006_an_unmatched_source_ref_is_an_explicit_not_found_not_an_error(db_session):
    _seed(db_session)

    missing = resolve_source_ref(db_session, "ehr:note:absent")

    assert missing.found is False
    assert bool(missing) is False
    assert missing.note_text is None
    assert missing.note_type is None
    assert missing.note_time is None


def test_ac007_the_report_exposes_provenance_failures_beside_the_row_counts(db_session):
    run = IngestRun(dataset_version="v", status="succeeded")
    db_session.add(run)
    db_session.flush()
    db_session.add(
        IngestFileResult(
            ingest_run_id=run.id,
            file_name="events.csv",
            status="pass",
            rows_loaded=3,
            rows_rejected=1,
            provenance_failures=1,
            error_detail="events.csv: provenance failure: event 'E9' is missing source_ref",
        )
    )
    db_session.commit()

    report = _report(db_session, run)

    line = report["files"][0]
    assert line["rows_loaded"] == 3
    assert line["rows_rejected"] == 1
    assert line["provenance_failures"] == 1
    assert "events.csv" in line["error"]
    assert "E9" in line["error"]
    assert "source_ref" in line["error"]

    failures = report["provenance_failures"]
    assert [entry["file"] for entry in failures] == ["events.csv"]
    assert failures[0]["count"] == 1
    assert "E9" in failures[0]["detail"]


def test_ac005_a_read_item_carries_every_provenance_field(db_session):
    patient = _seed(db_session)

    item = _timeline_items(db_session, patient)[0]

    for field in (
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
        "dataset_version",
    ):
        assert field in item, field
    assert item["event_id"] == "E1"
    assert item["source_type"] == "ehr"
    assert item["source_ref"] == "ehr:note:1"


def test_ac006_a_read_item_carries_the_note_its_source_ref_resolves_to(db_session):
    patient = _seed(db_session)

    item = _timeline_items(db_session, patient)[0]

    assert item["note_text"] == "Reports morning stiffness."
    assert item["note_type"] == "clinic_note"
    assert item["note_time"] is not None
