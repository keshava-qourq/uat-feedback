"""Encounter de-duplication: one real visit, however many sources describe it.

The dataset records the same real-world encounter twice -- once as an EHR row
and once as the claim it generated -- and a timeline that showed both would
tell the patient they were seen twice. This module is the one place that
decides which source rows describe the same encounter.

The rule, applied per patient and only across rows of *different*
`source_type` values (two EHR rows are two genuine events, never a duplicate
of each other):

1. **Compatible encounter reference.** Both rows carry an `encounter_ref` and,
   once the reference is normalised (its leading `Encounter/`, `enc:` or
   `claim:` qualifier dropped, surrounding whitespace removed, compared
   case-sensitively like every other text identifier in this system), the two
   references are equal.
2. **Time plus code plus provider.** Both rows carry an `event_time` no more
   than `TOLERANCE` (24 hours) apart, carry the same non-empty `code`, and
   carry the same `provider_org` -- or one of the two leaves the provider
   blank, which a claim row routinely does.

Two rows matching under either clause join the same encounter group; grouping
is transitive, so an EHR row, its claim and a second claim for the same visit
form one group. Nothing else merges: a row matching nothing is its own group
of one, so no timeline entry is ever invented that no source row supports.

The grouping is deterministic (rows are ordered by event time, then source
event id, before matching) and idempotent: `assign_groups` re-run over the
same data keeps the group id already stored on a member rather than minting a
new one.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Event

__all__ = [
    "TOLERANCE",
    "assign_groups",
    "group_rows",
    "merge_items",
    "normalise_encounter_ref",
    "visit_count",
]

#: How far apart two source rows may be dated and still be one visit.
TOLERANCE = timedelta(hours=24)

#: Reference qualifiers the two sources spell differently for one encounter.
_REF_PREFIXES = ("Encounter/", "encounter/", "enc:", "claim:", "ehr:")


def normalise_encounter_ref(value: Any) -> str:
    """An encounter reference without its source's own qualifier."""
    text = str(value or "").strip()
    for prefix in _REF_PREFIXES:
        if text.startswith(prefix):
            text = text[len(prefix) :]
            break
    return text.strip()


def _time(row: Any) -> datetime | None:
    return getattr(row, "event_time", None)


def _sort_key(row: Any) -> tuple[int, str, str]:
    when = _time(row)
    return (0 if when is not None else 1, when.isoformat() if when else "", row.source_event_id)


def _matches(left: Any, right: Any) -> bool:
    """Whether these two rows describe one encounter, under the documented rule."""
    if left.source_type == right.source_type:
        return False
    left_ref = normalise_encounter_ref(left.encounter_ref)
    right_ref = normalise_encounter_ref(right.encounter_ref)
    if left_ref and right_ref:
        return left_ref == right_ref
    left_time, right_time = _time(left), _time(right)
    if left_time is None or right_time is None:
        return False
    if abs(left_time - right_time) > TOLERANCE:
        return False
    if not (left.code and right.code) or left.code != right.code:
        return False
    left_org = (left.provider_org or "").strip()
    right_org = (right.provider_org or "").strip()
    return not left_org or not right_org or left_org == right_org


def group_rows(rows: list[Any]) -> list[list[Any]]:
    """`rows` of one patient split into encounter groups, oldest group first.

    Every row appears in exactly one group, and a group's rows keep the order
    they were matched in (oldest first).
    """
    groups: list[list[Any]] = []
    for row in sorted(rows, key=_sort_key):
        for group in groups:
            if any(_matches(row, member) for member in group):
                group.append(row)
                break
        else:
            groups.append([row])
    return groups


def _group_id(group: list[Any]) -> str:
    """The group's key: the one already stored on a member, else a new UUID."""
    for member in group:
        existing = getattr(member, "encounter_group_id", None)
        if existing:
            return existing
    return str(uuid.uuid4())


def assign_groups(db: Session, dataset_version: str | None = None) -> int:
    """Populate `events.encounter_group_id` for the loaded cohort.

    Returns how many groups were written. Safe to run twice: a second run
    recomputes the same groups and reuses the id already stored, so no row
    changes group and no duplicate entry appears.
    """
    query = select(Event)
    if dataset_version is not None:
        query = query.where(Event.dataset_version == dataset_version)
    rows = list(db.execute(query.order_by(Event.patient_id)).scalars())
    by_patient: dict[str, list[Event]] = {}
    for row in rows:
        by_patient.setdefault(row.patient_id, []).append(row)
    written = 0
    for patient_rows in by_patient.values():
        for group in group_rows(patient_rows):
            group_id = _group_id(group)
            for member in group:
                member.encounter_group_id = group_id
            written += 1
    db.commit()
    return written


def merge_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """One timeline entry per encounter, oldest first (AC-011, US-004-1).

    Each entry keeps every field of its earliest contributing row and adds
    `sources` (the distinct source types behind it, in a stable order),
    `merged_from` (the contributing `source_event_id`s) and
    `visit_count_contribution`, which is 1 for a merged encounter however
    many source rows it carries.
    """
    groups: dict[str, list[dict[str, Any]]] = {}
    order: list[str] = []
    for index, item in enumerate(items):
        key = str(item.get("encounter_group_id") or f"__ungrouped__{index}")
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(item)

    merged: list[dict[str, Any]] = []
    for key in order:
        members = groups[key]
        primary = dict(members[0])
        sources: list[str] = []
        for member in members:
            source = member.get("source_type")
            if source and source not in sources:
                sources.append(source)
        primary["sources"] = sources
        primary["merged_from"] = [
            member["source_event_id"] for member in members if member.get("source_event_id")
        ]
        primary["visit_count_contribution"] = 1
        merged.append(primary)
    return merged


def visit_count(items: list[dict[str, Any]]) -> int:
    """How many visits a list of merged timeline entries represents."""
    return sum(int(item.get("visit_count_contribution", 1)) for item in items)
