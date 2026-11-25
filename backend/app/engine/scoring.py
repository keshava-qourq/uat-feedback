"""Turning the criteria evaluation into a tier (US-012-1, AC-037..AC-040).

The engine's headline output is a tier word, never a number: `score_patient`
returns exactly one of the four names `app.engine.tiers` spells, and no bare
score or probability leaves this module.

Everything numeric comes from the active pack (NFR-019):

* `thresholds.reachable_history_months` gates the whole thing -- a patient
  whose reachable history (earliest reachable pre-cutoff item to the cutoff)
  is shorter than it is at "Insufficient history", never at the reassuring
  tier below it;
* the bands above that gate are the pack thresholds named by the tiers
  themselves (the lower-case spelling of each tier name), applied to the
  criteria evaluation `app.engine.criteria.evaluate_case` already produced.

No criterion, marker or condition name is written here: the sections of the
evaluation are read generically. Only pre-cutoff evidence is read, through
`app.engine.inputs.cutoff_date` / `is_pre_cutoff` (NFR-013).
"""

from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.engine.counter_evidence import apply_cap, counter_evidence
from app.engine.criteria import STATUS_MET, evaluate_case, pack_config
from app.engine.inputs import cutoff_date, is_pre_cutoff, item_date
from app.engine.tiers import TIER_HIGH, TIER_INSUFFICIENT_HISTORY, TIER_LOW, TIER_MODERATE
from app.models import Event, Patient

__all__ = ["reachable_history", "score_patient", "thresholds_in_force"]

#: The pack key holding the gate, as the pack spells it.
REACHABLE_HISTORY_MONTHS = "reachable_history_months"

#: The bands above the gate, highest first. Each reads the pack threshold
#: named by its own tier, so no threshold name is spelled twice.
BANDS: tuple[str, ...] = (TIER_HIGH, TIER_MODERATE)


def _thresholds(config: dict[str, Any] | None) -> dict[str, Any]:
    section = (config or {}).get("thresholds")
    return section if isinstance(section, dict) else {}


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _months_between(start: date, end: date) -> int:
    months = (end.year - start.year) * 12 + (end.month - start.month)
    if end.day < start.day:
        months -= 1
    return max(months, 0)


def _earliest_reachable(db: Session, patient_id: str, cutoff: date | None) -> date | None:
    """The date of the earliest item the engine may read for this patient."""
    dates = [
        item_date(row.event_time)
        for row in db.execute(select(Event).where(Event.patient_id == patient_id)).scalars()
        if is_pre_cutoff(row.event_time, cutoff, row.event_type)
    ]
    dated = [when for when in dates if when is not None]
    earliest = min(dated) if dated else None
    patient = db.get(Patient, patient_id)
    start = patient.reachable_history_start if patient is not None else None
    if earliest is None:
        return start
    if start is None:
        return earliest
    return max(earliest, start)


def reachable_history(db: Session, patient_id: str) -> dict[str, Any]:
    """How much history the engine can reach, against the threshold in force.

    `months`, `threshold_months` and `below_threshold` are read from the pack
    on every call, so editing the stored pack changes the answer with no code
    change (AC-040).
    """
    config = pack_config(db)
    threshold = _number(_thresholds(config).get(REACHABLE_HISTORY_MONTHS))
    cutoff = cutoff_date(db, patient_id)
    start = _earliest_reachable(db, patient_id, cutoff)
    months = _months_between(start, cutoff) if (start and cutoff) else None
    if threshold is None:
        below = False
    elif months is None:
        # Nothing reachable, or no cutoff to measure against: fail closed.
        below = True
    else:
        below = months < threshold
    return {
        "start": start.isoformat() if start else None,
        "months": months,
        "threshold_months": int(threshold) if threshold is not None else None,
        "below_threshold": below,
    }


def thresholds_in_force(db: Session) -> dict[str, Any]:
    """The thresholds the active pack declares right now (AC-040).

    Read on every call, so an edit through `PUT /api/admin/pack` is stated by
    the next evaluation report with no code change.
    """
    thresholds = _thresholds(pack_config(db))
    forced: dict[str, Any] = {REACHABLE_HISTORY_MONTHS: thresholds.get(REACHABLE_HISTORY_MONTHS)}
    for tier in BANDS:
        forced[tier.lower()] = thresholds.get(tier.lower())
    return forced


def _coverage(section: Any) -> float | None:
    """How fully one evaluated section of the criteria is answered, 0..1."""
    if isinstance(section, list):
        items = [item for item in section if isinstance(item, dict)]
        if not items:
            return None
        met = [item for item in items if item.get("status") == STATUS_MET]
        return len(met) / len(items)
    if isinstance(section, dict):
        threshold = _number(section.get("threshold"))
        total = _number(section.get("total"))
        if threshold is None or total is None or threshold <= 0:
            return None
        return min(total / threshold, 1.0)
    return None


def _band(evaluation: dict[str, Any], config: dict[str, Any] | None) -> str:
    """The tier the pack's bands give this evaluation, above the gate."""
    covered = [
        value
        for value in (_coverage(section) for section in evaluation.get("criteria", {}).values())
        if value is not None
    ]
    strength = max(covered) if covered else 0.0
    thresholds = _thresholds(config)
    for tier in BANDS:
        cut = _number(thresholds.get(tier.lower()))
        if cut is not None and strength >= cut:
            return tier
    return TIER_LOW


def _tier_reason(
    tier: str,
    history: dict[str, Any],
    counter: dict[str, Any],
    has_pack: bool,
) -> str:
    """Why this patient sits at this tier, in words -- never a bare number.

    The sentence is the one the worklist row, the case read and the referral
    packet all show, so a clinician never has to read a score to know why
    (AC-037).
    """
    if tier == TIER_INSUFFICIENT_HISTORY:
        if not has_pack:
            return "No condition logic is active, so this record cannot be judged yet."
        months, threshold = history.get("months"), history.get("threshold_months")
        if months is None:
            return (
                "No reachable history before the evaluation cutoff, so there is "
                "not enough record to judge this case."
            )
        return (
            f"Only {months} months of records are reachable, under the "
            f"{threshold}-month threshold, so this case cannot be judged yet."
        )
    capped = [item["label"] for item in counter["items"] if item.get("capped_to")]
    if capped:
        return f"Held at {tier} by counter-evidence: " + "; ".join(capped) + "."
    if tier == TIER_LOW:
        return "The reachable record does not show the patterns the criteria look for."
    return f"{tier}: the reachable record answers enough of the criteria to say so."


def score_patient(db: Session, patient_id: str) -> dict[str, Any]:
    """One patient's tier, the history behind it and the criteria it rests on.

    The headline is always a tier word from `app.engine.tiers`; no score or
    probability is returned (AC-037).
    """
    config = pack_config(db)
    evaluation = evaluate_case(db, patient_id)
    history = reachable_history(db, patient_id)

    counter = counter_evidence(db, patient_id)

    if config is None or history["below_threshold"]:
        tier = TIER_INSUFFICIENT_HISTORY
    else:
        # Counter-evidence is applied after the bands, and only ever lowers
        # the tier; it never overrides the Insufficient-history gate.
        tier = apply_cap(_band(evaluation, config), counter["cap"])

    thresholds = _thresholds(config)
    return {
        "patient_id": patient_id,
        "tier": tier,
        "tier_reason": _tier_reason(tier, history, counter, config is not None),
        "counter_evidence": counter["items"],
        "alternative_explanation": counter["alternative_explanation"],
        "cutoff_date": evaluation.get("cutoff_date"),
        "reachable_history": history,
        "criteria": evaluation.get("criteria", {}),
        "thresholds_in_force": {
            REACHABLE_HISTORY_MONTHS: history["threshold_months"],
            **{tier_name.lower(): thresholds.get(tier_name.lower()) for tier_name in BANDS},
        },
    }
