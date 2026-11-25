"""Counter-evidence rules, evaluated inside the scoring engine (US-012-2).

Every rule, its plain-language sentence, its effect, the tier that effect
names, the window it allows and the alternative explanation it offers are read
from the active pack's `counter_evidence` / `demotion_rules` sections
(NFR-019): nothing here names a condition, a clue or a marker.

A rule fires when one of the triggers it declares is found in this patient's
pre-cutoff record (NFR-013):

* `code_lists` -- a coded event whose code is in one of those pack lists;
* `intake_keys` -- a patient-reported answer to one of those questions;
* `clues` -- a row the free-text clue extractor already wrote for a note
  (`app.clue_extraction`), optionally pinned to one `value`.

Every fired rule is listed on its own, with the evidence that triggered it,
the cap it applied, and whether the pack still marks it as awaiting clinical
sign-off. A cap only ever lowers a tier, and it never replaces the
Insufficient-history state the reachable-history gate produces.
"""

from __future__ import annotations

import re
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.engine.criteria import INTAKE_SOURCE_TAG, pack_config
from app.engine.inputs import cutoff_date, is_pre_cutoff, item_date
from app.engine.tiers import TIER_INSUFFICIENT_HISTORY, WORKLIST_ORDER
from app.extraction_report import note_link
from app.models import Event, IntakeAnswer, NoteFinding
from app.provenance import resolve_source_ref

__all__ = ["apply_cap", "counter_evidence", "tier_rank"]

#: The pack sections this reads.
RULE_SECTION = "counter_evidence"
EFFECT_SECTION = "demotion_rules"

#: The tier ladder, lowest first. A cap may only move a tier down it.
LADDER: tuple[str, ...] = tuple(
    tier for tier in reversed(WORKLIST_ORDER) if tier != TIER_INSUFFICIENT_HISTORY
)

#: Month counts a sentence may spell out in words rather than digits.
WORD_MONTHS: dict[str, int] = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
}

_MONTHS = re.compile(r"(\d+|[a-z]+)\s+months?", re.IGNORECASE)

#: The source tag a note-derived evidence item carries.
NOTE_SOURCE_TAG = "note"


def tier_rank(tier: str | None) -> int:
    """Where a tier sits on the ladder. An unknown tier sorts at the bottom."""
    try:
        return LADDER.index(tier or "")
    except ValueError:
        return 0


def _mapping(config: dict[str, Any] | None, name: str) -> dict[str, Any]:
    section = (config or {}).get(name)
    return section if isinstance(section, dict) else {}


def _codes(config: dict[str, Any], keys: list[str]) -> set[str]:
    lists = _mapping(config, "code_lists")
    found: set[str] = set()
    for key in keys:
        entry = lists.get(key)
        if isinstance(entry, dict):
            found.update(str(code).strip() for code in entry.get("codes") or [])
    return found


def _months_stated(sentence: str) -> int | None:
    """The number of months a sentence states, when it states one."""
    match = _MONTHS.search(sentence or "")
    if match is None:
        return None
    token = match.group(1).lower()
    if token.isdigit():
        return int(token)
    return WORD_MONTHS.get(token)


def _within_window(rule: dict[str, Any], config: dict[str, Any], sentence: str) -> bool:
    """True unless the rule declares a window the sentence falls outside of."""
    key = rule.get("window_months")
    if not key:
        return True
    allowed = _mapping(config, "thresholds").get(str(key))
    stated = _months_stated(sentence)
    if not isinstance(allowed, (int, float)) or stated is None:
        # The wording itself places the onset in the period; with no number to
        # compare, the rule still fires.
        return True
    return stated <= float(allowed)


def _event_evidence(patient_id: str, row: Event) -> dict[str, Any]:
    when = item_date(row.event_time)
    return {
        "display": row.display or row.code or row.event_type,
        "date": when.isoformat() if when else None,
        "source_tag": row.source_type,
        "source_ref": row.source_ref,
        "note_link": note_link(patient_id, row.source_ref or ""),
    }


def _answer_evidence(row: IntakeAnswer) -> dict[str, Any]:
    when = item_date(row.answered_at)
    return {
        "display": f"{row.question_key}: {row.answer_value}",
        "date": when.isoformat() if when else None,
        "source_tag": INTAKE_SOURCE_TAG,
        "source_ref": f"{INTAKE_SOURCE_TAG}:{row.id}",
        "note_link": None,
    }


def _finding_evidence(patient_id: str, row: NoteFinding, when: Any) -> dict[str, Any]:
    moment = item_date(when)
    return {
        "display": row.quoted_sentence,
        "date": moment.isoformat() if moment else None,
        "source_tag": NOTE_SOURCE_TAG,
        "source_ref": row.source_ref,
        "note_link": note_link(patient_id, row.source_ref),
    }


def _pre_cutoff_records(db: Session, patient_id: str) -> tuple[list, list, list]:
    cutoff = cutoff_date(db, patient_id)
    events = [
        row
        for row in db.execute(
            select(Event).where(Event.patient_id == patient_id).order_by(Event.event_time)
        ).scalars()
        if is_pre_cutoff(row.event_time, cutoff, row.event_type)
    ]
    answers = [
        row
        for row in db.execute(
            select(IntakeAnswer).where(IntakeAnswer.patient_id == patient_id)
        ).scalars()
        if is_pre_cutoff(row.answered_at, cutoff)
    ]
    findings: list[tuple[NoteFinding, Any]] = []
    for row in db.execute(
        select(NoteFinding)
        .where(NoteFinding.patient_id == patient_id)
        .order_by(NoteFinding.clue_type)
    ).scalars():
        record = resolve_source_ref(db, row.source_ref, patient_id)
        if is_pre_cutoff(record.note_time, cutoff):
            findings.append((row, record.note_time))
    return events, answers, findings


def _triggered(
    rule: dict[str, Any],
    config: dict[str, Any],
    patient_id: str,
    events: list[Event],
    answers: list[IntakeAnswer],
    findings: list[tuple[NoteFinding, Any]],
) -> list[dict[str, Any]]:
    """The evidence items that fire this rule, empty when it does not fire."""
    evidence: list[dict[str, Any]] = []

    codes = _codes(config, list(rule.get("code_lists") or []))
    for row in events:
        if codes and (row.code or "").strip() in codes:
            evidence.append(_event_evidence(patient_id, row))

    intake_keys = {str(key).strip().lower() for key in rule.get("intake_keys") or []}
    for answer in answers:
        if str(answer.question_key or "").strip().lower() in intake_keys:
            evidence.append(_answer_evidence(answer))

    for wanted in rule.get("clues") or []:
        wanted = wanted if isinstance(wanted, dict) else {"clue": wanted}
        clue = str(wanted.get("clue") or "")
        value = wanted.get("value")
        for row, when in findings:
            if row.clue_type != clue:
                continue
            if value is not None and str(row.finding_value or "") != str(value):
                continue
            if not _within_window(rule, config, row.quoted_sentence):
                continue
            evidence.append(_finding_evidence(patient_id, row, when))

    return evidence


def _target_tier(rule: dict[str, Any], config: dict[str, Any]) -> str | None:
    """The tier this rule's effect names, read through `demotion_rules`."""
    effect = _mapping(config, EFFECT_SECTION).get(str(rule.get("effect") or ""))
    if not isinstance(effect, dict):
        return None
    field = effect.get("tier_from")
    target = rule.get(str(field)) if field else None
    return str(target) if target else None


def counter_evidence(db: Session, patient_id: str) -> dict[str, Any]:
    """Every counter-evidence rule this patient's pre-cutoff record fires."""
    config = pack_config(db) or {}
    rules = _mapping(config, RULE_SECTION)
    if not rules:
        return {"items": [], "cap": None, "alternative_explanation": None}

    events, answers, findings = _pre_cutoff_records(db, patient_id)
    items: list[dict[str, Any]] = []
    alternative: dict[str, Any] | None = None
    cap: str | None = None

    for key, raw in rules.items():
        rule = raw if isinstance(raw, dict) else {}
        evidence = _triggered(rule, config, patient_id, events, answers, findings)
        if not evidence:
            continue
        target = _target_tier(rule, config)
        items.append(
            {
                "key": key,
                "label": str(rule.get("label") or key),
                "plain_language": str(rule.get("plain_language") or rule.get("label") or key),
                "effect": str(rule.get("effect") or ""),
                "capped_to": target,
                "awaiting_sign_off": bool(rule.get("requires_sign_off")),
                "evidence": evidence,
            }
        )
        if target is not None and (cap is None or tier_rank(target) < tier_rank(cap)):
            cap = target
        stated = rule.get("alternative_explanation")
        if stated and alternative is None:
            alternative = {"label": str(stated), "from_rule": key}

    return {"items": items, "cap": cap, "alternative_explanation": alternative}


def apply_cap(tier: str, cap: str | None) -> str:
    """The tier after a cap: only ever lower, and never over Insufficient history."""
    if cap is None or tier == TIER_INSUFFICIENT_HISTORY:
        return tier
    return cap if tier_rank(cap) < tier_rank(tier) else tier
