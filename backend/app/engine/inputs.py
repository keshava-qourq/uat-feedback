"""A patient's leakage-safe engine input set (US-003-2, NFR-013).

One place decides what the engine may see about a patient: events dated
strictly before that patient's evaluation cutoff, plus the undated
family-history rows the non-functional requirement allows as the single
exception. The cutoff is read only through `app.labels.operational_labels`, so
no ground-truth column can reach an input, a feature or a screen.

Comparisons are made on the UTC calendar date, because no per-user time zone
is stored anywhere in the data model (behaviour rules).

A patient with no recorded cutoff is not dropped and nothing of theirs is
filtered: the input set says so (`has_cutoff: False`) and the guardrail
reports it.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any

from app.labels import operational_labels

__all__ = [
    "FAMILY_HISTORY_TYPES",
    "GROUND_TRUTH_KEYS",
    "cutoff_date",
    "filter_items",
    "ground_truth_keys_in",
    "input_set",
    "is_pre_cutoff",
    "item_date",
]

#: Ground truth: no input set, feature or rendered payload may carry any of
#: these, under this name or any other spelling of it (AC-008).
GROUND_TRUTH_KEYS: frozenset[str] = frozenset(
    {
        "archetype",
        "typicality",
        "clue_density",
        "hla_b27_true",
        "hla_b27",
        "axspa_label",
        "axspa",
        "simulated_diagnosis_date",
    }
)

#: Event types whose rows carry no date and are still admissible (NFR-013).
FAMILY_HISTORY_TYPES: tuple[str, ...] = ("family_history", "familyhistory", "family-history")


def cutoff_date(db, patient_id: str) -> date | None:
    """This patient's evaluation cutoff, read through the operational accessor."""
    return operational_labels(db, patient_id)["eval_cutoff_date"]


def item_date(value: Any) -> date | None:
    """The UTC calendar date of a timestamp, date or ISO-8601 string."""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        moment = value if value.tzinfo is not None else value.replace(tzinfo=UTC)
        return moment.astimezone(UTC).date()
    if isinstance(value, date):
        return value
    text = str(value).strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        try:
            return date.fromisoformat(text[:10])
        except ValueError:
            return None
    return item_date(parsed)


def _is_family_history(event_type: Any) -> bool:
    return str(event_type or "").strip().lower() in FAMILY_HISTORY_TYPES


def is_pre_cutoff(when: Any, cutoff: date | None, event_type: Any = None) -> bool:
    """True when this item may be used or shown for a patient with `cutoff`.

    The boundary is strict: an item dated exactly on the cutoff is excluded.
    An undated row is admissible only when it is family history. With no
    cutoff recorded, nothing is filtered.
    """
    if cutoff is None:
        return True
    moment = item_date(when)
    if moment is None:
        return _is_family_history(event_type)
    return moment < cutoff


def filter_items(
    items: list[dict[str, Any]],
    cutoff: date | None,
    *,
    time_key: str = "event_time",
    type_key: str = "event_type",
) -> list[dict[str, Any]]:
    """The items of `items` admissible before `cutoff`, in the order given."""
    return [
        item
        for item in items
        if is_pre_cutoff(item.get(time_key) or item.get("item_time"), cutoff, item.get(type_key))
    ]


def ground_truth_keys_in(payload: Any) -> list[str]:
    """Every ground-truth key found anywhere in `payload`, deduplicated."""
    found: list[str] = []

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if str(key).strip().lower() in GROUND_TRUTH_KEYS and key not in found:
                    found.append(str(key))
                walk(child)
        elif isinstance(value, (list, tuple)):
            for child in value:
                walk(child)

    walk(payload)
    return found


def input_set(db, patient_id: str) -> dict[str, Any]:
    """Everything the engine may read about one patient, and nothing else."""
    # Imported here: `app.routers.data` builds the stored events into the one
    # item shape the whole app reads (already cutoff-filtered through this
    # module), and it imports this module.
    from app.routers.data import _timeline_items

    patient = _patient(db, patient_id)
    cutoff = cutoff_date(db, patient_id) if patient is not None else None
    items = _timeline_items(db, patient) if patient is not None else []
    return {
        "patient_id": patient_id,
        "cutoff_date": cutoff.isoformat() if cutoff else None,
        "has_cutoff": cutoff is not None,
        "items": items,
    }


def _patient(db, patient_id: str):
    from app.models import Patient

    return db.get(Patient, patient_id)
