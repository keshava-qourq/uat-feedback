"""The cohort evaluation report: metric maths, split, and the route (AC-009).

Sensitivity and PPV are computed over a seeded cohort whose ground truth is
reachable only through `app.labels`' evaluation-only accessor, and
`GET /api/evaluation/runs/latest` serves those numbers to staff alone.
"""

from __future__ import annotations

import secrets
from datetime import UTC, date, datetime, timedelta

import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import evaluation
from app.labels import PatientLabel
from app.models import Event, Patient, User
from app.notice import SYNTHETIC_DATA_NOTICE
from app.security import hash_password

ROUTE = "/api/evaluation/runs/latest"

CUTOFF = date(2022, 1, 1)


@pytest.fixture
def password() -> str:
    return secrets.token_urlsafe(16)


def _user(db: Session, *, role: str, password: str, patient_id: str | None = None) -> User:
    user = User(
        email=f"{secrets.token_hex(6)}@example.invalid",
        password_hash=hash_password(password),
        role=role,
        patient_id=patient_id,
        is_active=True,
        must_set_password=False,
    )
    db.add(user)
    db.commit()
    return user


def _patient(
    db: Session,
    *,
    name: str,
    split: str,
    truth: bool,
    items: int,
    cutoff: date | None = CUTOFF,
) -> Patient:
    """One seeded patient: `items` pre-cutoff events and one ground-truth label."""
    patient = Patient(dataset_patient_id=name, dataset_version="v1", display_name=name)
    db.add(patient)
    db.commit()
    db.add(
        PatientLabel(
            patient_id=patient.id,
            dataset_version="v1",
            split=split,
            eval_cutoff_date=cutoff,
            archetype="classic",
            typicality="typical",
            clue_density=0.5,
            hla_b27_true=truth,
            axspa_label=truth,
        )
    )
    when = datetime(2020, 1, 1, tzinfo=UTC)
    for index in range(items):
        db.add(
            Event(
                patient_id=patient.id,
                source_event_id=f"{name}-E{index}",
                event_time=when + timedelta(days=index),
                event_type="encounter",
                source_type="ehr",
                source_ref=f"ehr:enc:{name}-{index}",
                dataset_version="v1",
            )
        )
    db.commit()
    return patient


def _seed_cohort(db: Session) -> None:
    """Two true positives, one false negative, one false positive, one true negative.

    Three patients are predicted positive (TP1, TP2, FP1), of which two are
    true: sensitivity = 2/3, PPV = 2/3.
    """
    _patient(db, name="TP1", split="test", truth=True, items=4)
    _patient(db, name="TP2", split="test", truth=True, items=3)
    _patient(db, name="FN1", split="test", truth=True, items=1)
    _patient(db, name="FP1", split="test", truth=False, items=5)
    _patient(db, name="TN1", split="test", truth=False, items=0)


def test_ac009_sensitivity_and_ppv_are_computed_over_the_seeded_cohort(db_session):
    _seed_cohort(db_session)
    frame = evaluation.cohort_frame(db_session)
    assert len(frame) == 5

    scores = evaluation.metrics(frame)
    assert scores["sensitivity"] == pytest.approx(2 / 3)
    assert scores["ppv"] == pytest.approx(2 / 3)


def test_ac009_a_perfect_cohort_scores_one_on_both_measures(db_session):
    _patient(db_session, name="A", split="train", truth=True, items=4)
    _patient(db_session, name="B", split="train", truth=False, items=0)

    scores = evaluation.metrics(evaluation.cohort_frame(db_session))
    assert scores["sensitivity"] == pytest.approx(1.0)
    assert scores["ppv"] == pytest.approx(1.0)


def test_ac009_an_undefined_measure_is_none_rather_than_zero(db_session):
    """With no positive truth there is no sensitivity, and with no positive
    prediction there is no PPV: the report says so instead of inventing a 0."""
    assert evaluation.metrics(pd.DataFrame(columns=["split", "truth", "predicted"])) == {
        "sensitivity": None,
        "ppv": None,
    }
    _patient(db_session, name="N1", split="val", truth=False, items=0)
    scores = evaluation.metrics(evaluation.cohort_frame(db_session))
    assert scores == {"sensitivity": None, "ppv": None}


def test_ac009_ground_truth_is_read_through_the_evaluation_only_accessor(db_session):
    """The truth column comes from the store, not from anything operational."""
    _patient(db_session, name="TP1", split="test", truth=True, items=4)
    _patient(db_session, name="TN1", split="test", truth=False, items=0)

    frame = evaluation.cohort_frame(db_session).set_index("patient_id")
    truths = {name: bool(value) for name, value in frame["truth"].items()}
    assert sorted(truths.values()) == [False, True]


def test_the_report_states_the_cohort_split_it_evaluated_on(db_session):
    _seed_cohort(db_session)
    report = evaluation.latest_report(db_session)
    assert report["split"] == "test"
    assert report["run"]["split"] == "test"
    assert report["run"]["split_counts"] == {"test": 5}
    assert report["run"]["patient_count"] == 5


def test_the_report_names_a_mixed_cohort_rather_than_one_of_its_splits(db_session):
    _patient(db_session, name="A", split="train", truth=True, items=4)
    _patient(db_session, name="B", split="val", truth=False, items=0)
    assert evaluation.latest_report(db_session)["split"] == evaluation.MIXED_SPLIT


def _token(client: TestClient, user: User, password: str) -> str:
    response = client.post("/api/auth/login", json={"email": user.email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["token"]


def test_ac009_the_route_is_401_unauthenticated(client):
    response = client.get(ROUTE)
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_ac009_the_route_is_403_for_a_patient_token(client, db_session, password):
    patient = _patient(db_session, name="P1", split="test", truth=True, items=4)
    user = _user(db_session, role="patient", password=password, patient_id=patient.id)
    response = client.get(
        ROUTE, headers={"Authorization": f"Bearer {_token(client, user, password)}"}
    )
    assert response.status_code == 403
    assert response.json() == {"detail": "Not allowed"}


def test_ac009_staff_get_sensitivity_ppv_the_split_and_the_synthetic_notice(
    client, db_session, password
):
    _seed_cohort(db_session)
    user = _user(db_session, role="clinician", password=password)
    response = client.get(
        ROUTE, headers={"Authorization": f"Bearer {_token(client, user, password)}"}
    )
    assert response.status_code == 200, response.text
    body = response.json()

    assert body["notice"] == SYNTHETIC_DATA_NOTICE
    assert body["split"] == "test"
    values = {metric["key"]: metric["value"] for metric in body["metrics"]}
    assert values["sensitivity"] == pytest.approx(2 / 3)
    assert values["ppv"] == pytest.approx(2 / 3)


def test_ac009_the_response_carries_no_per_patient_ground_truth_value(client, db_session, password):
    _seed_cohort(db_session)
    user = _user(db_session, role="clinician", password=password)
    response = client.get(
        ROUTE, headers={"Authorization": f"Bearer {_token(client, user, password)}"}
    )
    text = response.text.lower()
    for column in ("archetype", "typicality", "clue_density", "hla_b27", "axspa_label"):
        assert column not in text
