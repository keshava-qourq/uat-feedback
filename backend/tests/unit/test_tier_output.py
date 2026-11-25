"""US-012-3: the tier, the reachable-history state and the thresholds, as served.

The payload builders are exercised directly against a database session: the
worklist row, the case read, the referral packet and the evaluation report's
thresholds. Every threshold and code is read back from the active pack, never
spelled out here (NFR-019).
"""

from __future__ import annotations

import io
from datetime import UTC, date, datetime
from typing import Any

from app.engine.criteria import pack_config
from app.engine.scoring import REACHABLE_HISTORY_MONTHS, thresholds_in_force
from app.engine.tiers import TIER_INSUFFICIENT_HISTORY, WORKLIST_ORDER, worklist_rank
from app.labels import PatientLabel
from app.models import Event, Patient
from app.routers.data import _worklist_row, case_read, referral_packet_pdf, worklist

CUTOFF = date(2022, 1, 1)
LONG_AGO = datetime(2015, 1, 1, tzinfo=UTC)
#: Six months before the cutoff: well under any sane reachable-history gate.
RECENT = datetime(2021, 7, 1, tzinfo=UTC)


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
    db.add(
        Event(
            patient_id=patient.id,
            source_event_id=f"{name}-base",
            event_time=earliest,
            event_type="observation",
            code="ZZZ-not-in-any-code-list",
            display="A recorded finding",
            source_type="ehr",
            source_ref=f"ehr:{name}-base",
            dataset_version="v",
        )
    )
    db.commit()
    return patient


def _pdf_text(data: bytes) -> str:
    import pypdf

    reader = pypdf.PdfReader(io.BytesIO(data))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


# ----------------------------------------------------------------- worklist


def test_ac037_the_worklist_row_states_the_tier_and_its_reachable_history(db_session) -> None:
    """[AC-037] The row carries the four fields the contract names."""
    patient = _patient(db_session, "short", earliest=RECENT)

    row = _worklist_row(db_session, patient)

    assert row["tier"] in WORKLIST_ORDER
    assert isinstance(row["tier_reason"], str) and row["tier_reason"].strip()
    assert row["tier"] == TIER_INSUFFICIENT_HISTORY
    assert row["below_reachable_history_threshold"] is True
    assert row["reachable_history_months"] == 6
    assert isinstance(row["counter_evidence_count"], int)


def test_ac037_the_worklist_row_presents_no_bare_score(db_session) -> None:
    """[AC-037] No numeric score or probability is served for a patient."""
    patient = _patient(db_session, "scored")

    row = _worklist_row(db_session, patient)

    for key in ("score", "probability", "risk_score", "percentage"):
        assert key not in row
    assert not _is_number(row["tier"])


def test_ac037_the_worklist_is_ordered_by_the_tier_rank(db_session) -> None:
    """[AC-037] High, Moderate, Insufficient history, Low -- never alphabetical."""
    _patient(db_session, "aaa-short", earliest=RECENT)
    _patient(db_session, "zzz-long")

    rows = worklist(user=None, db=db_session)["items"]

    ranks = [worklist_rank(row["tier"]) for row in rows]
    assert ranks == sorted(ranks)


# ---------------------------------------------------------------- case read


def test_ac037_the_case_read_carries_the_tier_and_the_history_it_was_judged_against(
    db_session,
) -> None:
    """[AC-037, AC-040] tier, tier_reason, reachable_history, counter_evidence."""
    patient = _patient(db_session, "case", earliest=RECENT)

    body = case_read(patient.id, user=None, db=db_session)

    assert body["tier"] == TIER_INSUFFICIENT_HISTORY
    assert isinstance(body["tier_reason"], str) and body["tier_reason"].strip()
    reachable = body["reachable_history"]
    assert set(reachable) == {"months", "threshold_months", "below_threshold"}
    assert (
        reachable["threshold_months"]
        == pack_config(db_session)["thresholds"][REACHABLE_HISTORY_MONTHS]
    )
    assert reachable["below_threshold"] is True
    assert isinstance(body["counter_evidence"], list)
    assert body["alternative_explanation"] is None
    # The sections this ticket builds on are still there.
    assert "criteria" in body and "extracted_evidence" in body
    assert body["notice"]


# ----------------------------------------------------------------- the PDF


def test_ac039_the_referral_packet_states_insufficient_history_and_never_low(
    db_session,
) -> None:
    """[AC-039] The export never calls such a patient Low."""
    patient = _patient(db_session, "packet", earliest=RECENT)

    text = _pdf_text(referral_packet_pdf(patient.id, user=None, db=db_session).body)

    lowered = text.lower()
    assert "insufficient history" in lowered
    for marker in ("tier: low", "status: low", "likelihood: low"):
        assert marker not in lowered


# ---------------------------------------------------------- the thresholds


def test_ac040_the_thresholds_in_force_are_read_from_the_active_pack(db_session) -> None:
    """[AC-040] Every threshold the report states comes from the pack."""
    declared = pack_config(db_session)["thresholds"]

    forced = thresholds_in_force(db_session)

    assert forced[REACHABLE_HISTORY_MONTHS] == declared[REACHABLE_HISTORY_MONTHS]
    assert forced["high"] == declared["high"]
    assert forced["moderate"] == declared["moderate"]
