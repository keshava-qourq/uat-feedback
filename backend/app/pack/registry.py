"""The condition-pack registry: declarative packs, validated, reloadable.

A pack is a data file under `app/pack/packs/` -- code lists, signal
definitions, criteria, counter-evidence and demotion rules, tier thresholds,
suggested workup items with their reasoning, the patient-facing copy strings
and the prohibited-term list. Nothing in this module names a condition, a
marker, a criterion or a sentence: every accessor takes a key and returns
whatever the data file carries, so all condition logic lives in the pack and
changing a code list, a threshold or a wording needs no code deployment
(NFR-019).

Which pack is active is configuration:

* `CONDITION_PACK_ENABLED=false` -- no pack is active, whatever else is set.
* `CONDITION_PACK_KEY` unset or blank -- no pack is active.

"No pack active" is a first-class state: the application starts, `/health`
says so, and the generic ingest and timeline paths are untouched.

`reload()` drops the cache, so an edited pack file takes effect in a running
process.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

PACKS_DIR = Path(__file__).resolve().parent / "packs"

#: The sections every pack declares, and what each of their items must carry.
#: `None` means "any value"; a tuple is the set of accepted Python types.
SECTION_SCHEMA: dict[str, dict[str, Any]] = {
    "code_lists": {"system": (str,), "codes": (list,)},
    "signals": {"label": (str,)},
    "criteria": {"label": (str,), "kind": (str,)},
    "counter_evidence": {"label": (str,), "effect": (str,)},
    "workup_items": {"label": (str,), "reasoning": (str,)},
}

#: Sections that are a flat mapping of key -> scalar.
SCALAR_SECTIONS: dict[str, tuple[type, ...]] = {
    "thresholds": (int, float),
    "copy": (str,),
}

REQUIRED_TOP_LEVEL: dict[str, tuple[type, ...]] = {
    "pack_key": (str,),
    "version": (int,),
    "code_lists": (dict,),
    "signals": (dict,),
    "criteria": (dict,),
    "counter_evidence": (dict,),
    "thresholds": (dict,),
    "workup_items": (dict,),
    "copy": (dict,),
    "prohibited_terms": (list,),
}


class PackValidationError(ValueError):
    """A pack file that does not match the schema, naming the offending key."""

    def __init__(self, key: str, problem: str) -> None:
        super().__init__(f"{key}: {problem}")
        self.key = key
        self.problem = problem


def _check(condition: bool, key: str, problem: str) -> None:
    if not condition:
        raise PackValidationError(key, problem)


def validate(data: Any) -> dict[str, Any]:
    """Return `data` when it is a valid pack; raise naming the bad key otherwise."""
    _check(isinstance(data, dict), "<pack>", "a pack must be a mapping")
    for key, types in REQUIRED_TOP_LEVEL.items():
        _check(key in data, key, "is required and missing")
        _check(
            isinstance(data[key], types) and not isinstance(data[key], bool),
            key,
            f"must be {' or '.join(t.__name__ for t in types)}",
        )
    for section, fields in SECTION_SCHEMA.items():
        for item_key, item in data[section].items():
            path = f"{section}.{item_key}"
            _check(isinstance(item, dict), path, "must be a mapping")
            for field, types in fields.items():
                _check(field in item, f"{path}.{field}", "is required and missing")
                _check(
                    isinstance(item[field], types),
                    f"{path}.{field}",
                    f"must be {' or '.join(t.__name__ for t in types)}",
                )
    for section, types in SCALAR_SECTIONS.items():
        for item_key, value in data[section].items():
            _check(
                isinstance(value, types) and not isinstance(value, bool),
                f"{section}.{item_key}",
                f"must be {' or '.join(t.__name__ for t in types)}",
            )
    for index, term in enumerate(data["prohibited_terms"]):
        _check(isinstance(term, str), f"prohibited_terms[{index}]", "must be str")
    return data


@dataclass(frozen=True)
class Pack:
    """One loaded pack. Every accessor is generic: it takes a key."""

    key: str
    version: int
    data: dict[str, Any]

    # -- sections -----------------------------------------------------------
    def section(self, name: str) -> Any:
        """One top-level section, or None when the pack does not declare it."""
        return self.data.get(name)

    def _mapping(self, name: str) -> dict[str, Any]:
        value = self.data.get(name)
        return value if isinstance(value, dict) else {}

    def _item(self, section: str, key: str) -> Any:
        return self._mapping(section).get(key)

    def code_lists(self) -> dict[str, Any]:
        return self._mapping("code_lists")

    def code_list(self, key: str) -> Any:
        return self._item("code_lists", key)

    def signals(self) -> dict[str, Any]:
        return self._mapping("signals")

    def signal(self, key: str) -> Any:
        return self._item("signals", key)

    def criteria(self) -> dict[str, Any]:
        return self._mapping("criteria")

    def criterion(self, key: str) -> Any:
        return self._item("criteria", key)

    def counter_evidence(self) -> dict[str, Any]:
        return self._mapping("counter_evidence")

    def counter_evidence_rule(self, key: str) -> Any:
        return self._item("counter_evidence", key)

    def thresholds(self) -> dict[str, Any]:
        return self._mapping("thresholds")

    def threshold(self, key: str) -> Any:
        return self._item("thresholds", key)

    def workup_items(self) -> dict[str, Any]:
        return self._mapping("workup_items")

    def workup_item(self, key: str) -> Any:
        return self._item("workup_items", key)

    def copy(self) -> dict[str, Any]:
        return self._mapping("copy")

    def copy_text(self, key: str, default: str = "") -> str:
        value = self._item("copy", key)
        return default if value is None else str(value)

    def prohibited_terms(self) -> list[str]:
        value = self.data.get("prohibited_terms")
        return list(value) if isinstance(value, list) else []


_cache: dict[str, Pack] = {}


def _pack_path(key: str) -> Path:
    return PACKS_DIR / f"{key}.yaml"


def list_packs() -> list[str]:
    """The keys of every pack file present, sorted."""
    if not PACKS_DIR.is_dir():
        return []
    return sorted(path.stem for path in PACKS_DIR.glob("*.yaml"))


def load_pack(key: str) -> Pack:
    """The pack named `key`, validated. Raises `PackValidationError` when malformed."""
    cached = _cache.get(key)
    if cached is not None:
        return cached
    path = _pack_path(key)
    if not path.is_file():
        raise PackValidationError(key, "no pack file with this key")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:  # a file that is not parseable names itself
        raise PackValidationError(key, f"is not readable data ({exc})") from exc
    validate(data)
    pack = Pack(key=str(data["pack_key"]), version=int(data["version"]), data=data)
    _cache[key] = pack
    return pack


def reload() -> None:
    """Drop the cache so the next read picks the files up again (NFR-019)."""
    _cache.clear()


def pack_enabled() -> bool:
    """Whether packs are switched on at all (`CONDITION_PACK_ENABLED`)."""
    return (os.getenv("CONDITION_PACK_ENABLED") or "true").strip().lower() not in {
        "false",
        "0",
        "no",
        "off",
    }


def active_pack_key() -> str | None:
    """The configured active pack key, or None when no pack is active."""
    if not pack_enabled():
        return None
    return (os.getenv("CONDITION_PACK_KEY") or "").strip() or None


def get_active_pack() -> Pack | None:
    """The active pack, or None when configuration says no pack is active."""
    key = active_pack_key()
    return None if key is None else load_pack(key)


def active_pack_status() -> dict[str, Any]:
    """What `/health` and the startup log report about the pack."""
    key = active_pack_key()
    return {"active": key is not None, "key": key}


def log_active_pack() -> None:
    """One startup line naming the active pack, or saying none is."""
    key = active_pack_key()
    if key is None:
        logger.info("no condition pack is active")
    else:
        logger.info("condition pack active: %s", key)
