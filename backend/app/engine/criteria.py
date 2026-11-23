"""Scoring a patient against the active condition pack's criteria (US-010-1).

Every criterion name, every point item, every points value and the referral
threshold are read from the pack (NFR-019): nothing here names a condition, a
criterion or a marker. The pack declares signals (code lists and/or intake
keys), criteria of kind `set` (entry / required / any_of) and of kind `points`
(item -> points, with a `pass_score`), and this module turns them into the
met / not_met / unknown listing the case read serves.

Only pre-cutoff evidence is ever read: events and intake answers are filtered
through `app.engine.inputs.is_pre_cutoff` against the patient's own cutoff, so
no item dated on or after it can appear (NFR-013).

An item is `unknown` when nothing in the record can answer it -- a test that
was never done, a question that was never asked -- and then it carries a
`needed` string saying what would. An unknown item is never counted into the
points total.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.engine.inputs import cutoff_date, is_pre_cutoff, item_date
from app.models import Event, IntakeAnswer
from app.pack import active_pack
from app.pack import registry as pack_registry

__all__ = ["STATUS_MET", "STATUS_NOT_MET", "STATUS_UNKNOWN", "evaluate_case", "pack_config"]

STATUS_MET = "met"
STATUS_NOT_MET = "not_met"
STATUS_UNKNOWN = "unknown"

#: The source tag an intake answer carries: the patient told us themselves.
INTAKE_SOURCE_TAG = "patient"

#: Answer values that mean "no". Everything else present means "yes".
NEGATIVE_ANSWERS = frozenset({"", "no", "false", "0", "none", "never", "n"})

#: What the pack calls its two kinds of criterion.
KIND_SET = "set"
KIND_POINTS = "points"


# ----------------------------------------------------------------- the pack


def pack_config(db: Session) -> dict[str, Any] | None:
    """The active pack's configuration data, or None when no pack is active."""
    if not pack_registry.pack_enabled():
        return None
    stored = active_pack(db)
    key = pack_registry.active_pack_key()
    if key is None:
        keys = pack_registry.list_packs()
        key = keys[0] if len(keys) == 1 else None
    shipped: dict[str, Any] | None = None
    if key is not None:
        try:
            shipped = pack_registry.load_pack(key).data
        except pack_registry.PackValidationError:
            shipped = None
    if stored is None:
        return shipped
    config = dict(stored.config)
    # A stored row written before a section shipped must not hide that section:
    # the shipped file supplies whatever the stored version does not declare.
    for name, value in (shipped or {}).items():
        if config.get(name) is None:
            config[name] = value
    return config


def _mapping(config: dict[str, Any], name: str) -> dict[str, Any]:
    value = config.get(name)
    return value if isinstance(value, dict) else {}


# ------------------------------------------------------------- the evidence


def _event_evidence(row: Event) -> dict[str, Any]:
    when = item_date(row.event_time)
    return {
        "event_id": row.source_event_id,
        "display": row.display or row.code or row.event_type,
        "date": when.isoformat() if when else None,
        "source_tag": row.source_type,
    }


def _answer_evidence(row: IntakeAnswer) -> dict[str, Any]:
    when = item_date(row.answered_at)
    return {
        "event_id": row.id,
        "display": f"{row.question_key}: {row.answer_value}",
        "date": when.isoformat() if when else None,
        "source_tag": INTAKE_SOURCE_TAG,
    }


def _answers_question(question_key: Any, intake_keys: list[str]) -> bool:
    """True when this answer answers one of the signal's intake questions.

    A dataset spells a question out more fully than the pack names it
    (`<key>_minutes`, `<key>_days`), so a key the pack names is matched
    either exactly or as the leading part of the answered question.
    """
    asked = str(question_key or "").strip().lower()
    return any(
        asked == str(key).strip().lower() or asked.startswith(f"{str(key).strip().lower()}_")
        for key in intake_keys
    )


def _is_positive_answer(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return value > 0
    return str(value).strip().lower() not in NEGATIVE_ANSWERS


# -------------------------------------------------------------- the signals


def _codes(config: dict[str, Any], keys: list[str]) -> set[str]:
    lists = _mapping(config, "code_lists")
    found: set[str] = set()
    for key in keys:
        entry = lists.get(key)
        if isinstance(entry, dict):
            found.update(str(code).strip() for code in entry.get("codes") or [])
    return found


def _signal(
    config: dict[str, Any],
    key: str,
    events: list[Event],
    answers: list[IntakeAnswer],
) -> dict[str, Any]:
    """One signal's status, its evidence when met, and what would answer it."""
    definition = _mapping(config, "signals").get(key)
    definition = definition if isinstance(definition, dict) else {}
    label = str(definition.get("label") or key)
    code_keys = list(definition.get("code_lists") or [])
    intake_keys = list(definition.get("intake_keys") or [])
    positive_values = {
        str(value).strip().lower() for value in definition.get("positive_values") or []
    }
    minimum = int(definition.get("min_occurrences") or 1)

    codes = _codes(config, code_keys)
    matches = [row for row in events if (row.code or "").strip() in codes] if codes else []
    unknown_because: list[str] = []

    if positive_values:
        positive = [
            row for row in matches if str(row.value or "").strip().lower() in positive_values
        ]
        if positive:
            return _result(STATUS_MET, label, _event_evidence(positive[0]))
        if not matches:
            unknown_because.append(f"a recorded result for: {label}")
    elif codes:
        if len(matches) >= minimum:
            return _result(STATUS_MET, label, _event_evidence(matches[minimum - 1]))

    given = [row for row in answers if _answers_question(row.question_key, intake_keys)]
    for row in given:
        if _is_positive_answer(row.answer_value):
            return _result(STATUS_MET, label, _answer_evidence(row))
    if intake_keys and not given:
        unknown_because.append("an answer to: " + ", ".join(intake_keys))

    if unknown_because:
        return _result(
            STATUS_UNKNOWN,
            label,
            None,
            needed=f"{label} is unanswered: " + "; ".join(unknown_because),
        )
    return _result(STATUS_NOT_MET, label, None)


def _result(
    status: str, label: str, evidence: dict[str, Any] | None, needed: str | None = None
) -> dict[str, Any]:
    return {"label": label, "status": status, "evidence": evidence, "needed": needed}


def _signals(config: dict[str, Any], db: Session, patient_id: str) -> dict[str, dict[str, Any]]:
    """Every signal the pack declares, evaluated from pre-cutoff records only."""
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
            select(IntakeAnswer)
            .where(IntakeAnswer.patient_id == patient_id)
            .order_by(IntakeAnswer.answered_at)
        ).scalars()
        if is_pre_cutoff(row.answered_at, cutoff)
    ]
    return {key: _signal(config, key, events, answers) for key in _mapping(config, "signals")}


# ------------------------------------------------------------- the criteria


def _status_of(signals: dict[str, dict[str, Any]], key: str) -> str:
    return signals.get(key, {}).get("status", STATUS_UNKNOWN)


def _set_criterion(
    key: str, definition: dict[str, Any], signals: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    """A `set` criterion: entry and required signals plus an any_of quorum."""
    mandatory = [*(definition.get("entry") or []), *(definition.get("required") or [])]
    any_of = definition.get("any_of") if isinstance(definition.get("any_of"), dict) else {}
    quorum = int(any_of.get("min") or 0)
    optional = list(any_of.get("signals") or [])

    met = [name for name in mandatory if _status_of(signals, name) == STATUS_MET]
    unknown = [name for name in mandatory if _status_of(signals, name) == STATUS_UNKNOWN]
    any_met = [name for name in optional if _status_of(signals, name) == STATUS_MET]
    any_unknown = [name for name in optional if _status_of(signals, name) == STATUS_UNKNOWN]

    label = str(definition.get("label") or key)
    if len(met) == len(mandatory) and len(any_met) >= quorum:
        evidence = next(
            (signals[name]["evidence"] for name in [*met, *any_met] if signals[name]["evidence"]),
            None,
        )
        return {
            "key": key,
            "label": label,
            "status": STATUS_MET,
            "evidence": evidence,
            "needed": None,
        }

    reachable = (
        len(met) + len(unknown) == len(mandatory) and len(any_met) + len(any_unknown) >= quorum
    )
    if reachable:
        missing = [signals[name]["label"] for name in [*unknown, *any_unknown]]
        return {
            "key": key,
            "label": label,
            "status": STATUS_UNKNOWN,
            "evidence": None,
            "needed": "Still unanswered: " + "; ".join(missing),
        }
    return {"key": key, "label": label, "status": STATUS_NOT_MET, "evidence": None, "needed": None}


def _point_items(
    definition: dict[str, Any], signals: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    items = definition.get("items") if isinstance(definition.get("items"), dict) else {}
    listed: list[dict[str, Any]] = []
    for key, points in items.items():
        signal = signals.get(key) or _result(
            STATUS_UNKNOWN, key, None, needed=f"a record of: {key}"
        )
        listed.append(
            {
                "key": key,
                "label": signal["label"],
                "status": signal["status"],
                "points": int(points),
                "evidence": signal["evidence"],
                "needed": signal["needed"],
            }
        )
    return listed


def _first_token(key: str) -> str:
    return str(key).split("_", 1)[0]


def evaluate_case(db: Session, patient_id: str) -> dict[str, Any]:
    """The case read's body for one patient: every criterion and point item.

    The section names, the item labels, the points and the threshold all come
    from the pack; with no pack active the sections are empty.
    """
    config = pack_config(db)
    cutoff = cutoff_date(db, patient_id)
    body: dict[str, Any] = {
        "patient_id": patient_id,
        "cutoff_date": cutoff.isoformat() if cutoff else None,
        "criteria": {},
    }
    if config is None:
        return body

    signals = _signals(config, db, patient_id)
    criteria = _mapping(config, "criteria")
    set_keys = [key for key, item in criteria.items() if (item or {}).get("kind") == KIND_SET]
    point_keys = [key for key, item in criteria.items() if (item or {}).get("kind") == KIND_POINTS]

    if set_keys:
        section = f"{_first_token(set_keys[0])}_referral"
        body["criteria"][section] = [
            _set_criterion(key, criteria[key], signals) for key in set_keys
        ]
    if point_keys:
        definition = criteria[point_keys[0]]
        items = _point_items(definition, signals)
        body["criteria"][_first_token(point_keys[0])] = {
            "items": items,
            # Met points only: an unknown item is never counted (AC-032).
            "total": sum(item["points"] for item in items if item["status"] == STATUS_MET),
            "threshold": int(definition.get("pass_score") or 0),
        }
    return body
