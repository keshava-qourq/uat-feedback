"""The post-cutoff guardrail, run over the whole loaded cohort (AC-029, AC-008).

Two things are checked, for every patient in the loaded cohort:

1. nothing the engine reads or a screen renders is dated on or after that
   patient's evaluation cutoff -- an undated family-history row being the one
   exception NFR-013 allows;
2. no input set or rendered payload carries a ground-truth column, under any
   spelling of its name.

Zero violations is the only passing state. A patient with no cutoff recorded
has no boundary to cross, so nothing of theirs is filtered and nothing of
theirs can be post-cutoff: they are named in `unchecked` rather than silently
dropped from the sweep.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import select

from app.engine.inputs import (
    cutoff_date,
    ground_truth_keys_in,
    input_set,
    is_pre_cutoff,
    item_date,
)
from app.guardrails.result import GuardrailResult
from app.models import Patient

GUARDRAIL = "post_cutoff"

#: The keys an item carries its date under, in any payload this app renders.
TIME_KEYS = ("item_time", "event_time", "note_time", "item_date", "answered_at")

__all__ = [
    "GUARDRAIL",
    "check_cohort",
    "check_patient",
    "check_payload",
    "unchecked_patients",
]


def _dated_items(payload: Any) -> list[dict[str, Any]]:
    """Every dict in `payload` that carries a date under one of TIME_KEYS."""
    found: list[dict[str, Any]] = []

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            if any(key in value for key in TIME_KEYS):
                found.append(value)
            for child in value.values():
                walk(child)
        elif isinstance(value, (list, tuple)):
            for child in value:
                walk(child)

    walk(payload)
    return found


def _when(item: dict[str, Any]) -> Any:
    for key in TIME_KEYS:
        if item.get(key):
            return item[key]
    return None


def check_payload(
    patient_id: str, cutoff: date | None, payload: Any, where: str = ""
) -> GuardrailResult:
    """Every leakage violation in one payload for one patient."""
    result = GuardrailResult.passing(GUARDRAIL)
    place = f"patient {patient_id}" + (f" {where}" if where else "")
    if cutoff is not None:
        for item in _dated_items(payload):
            if is_pre_cutoff(_when(item), cutoff, item.get("event_type")):
                continue
            when = item_date(_when(item))
            name = item.get("event_id") or item.get("source_ref") or item.get("id") or "item"
            result = result.with_violation(
                where=f"{place} item {name}",
                detail=(
                    f"{item.get('event_type') or 'item'} dated "
                    f"{when.isoformat() if when else 'undated'} is not before the "
                    f"cutoff {cutoff.isoformat()}"
                ),
            )
    for key in ground_truth_keys_in(payload):
        result = result.with_violation(
            where=place,
            detail=f"the payload carries the ground-truth column '{key}'",
        )
    return result


def check_patient(db, patient: Patient) -> GuardrailResult:
    """The guardrail over one patient's engine input set."""
    cutoff = cutoff_date(db, patient.id)
    return check_payload(patient.id, cutoff, input_set(db, patient.id), "input set")


def _cohort(db) -> list[Patient]:
    return list(db.execute(select(Patient).order_by(Patient.display_name)).scalars())


def unchecked_patients(db) -> list[str]:
    """The patients with no cutoff recorded: nothing of theirs is filtered."""
    return [patient.id for patient in _cohort(db) if cutoff_date(db, patient.id) is None]


def check_cohort(db) -> GuardrailResult:
    """The guardrail over every loaded patient; `ok` only at zero violations."""
    violations = tuple(
        violation for patient in _cohort(db) for violation in check_patient(db, patient).violations
    )
    return GuardrailResult(guardrail=GUARDRAIL, violations=violations)
