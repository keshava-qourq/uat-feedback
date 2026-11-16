"""Resolving the active condition pack, or reporting that there is none.

The architecture requires the app to start cleanly with no pack active: a
fresh database has no `condition_packs` row, every screen must still render,
and the scoring engine falls back to its rules-only path. So "no pack" is a
first-class answer here, never an exception.

Only the resolution is scaffolded. Validating a pack's contents, writing a new
version and recording the change log belong to the admin-pack ticket; the
accessors below read whatever `config` JSON the active row carries.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ConditionPack


@dataclass(frozen=True)
class ActivePack:
    """The enabled pack of highest version, as the engine and the API read it."""

    pack_key: str
    version: int
    config: dict[str, Any]
    awaiting_review: dict[str, Any]

    def section(self, name: str, default: Any = None) -> Any:
        """One top-level section of the pack's config, e.g. "criteria"."""
        value = self.config.get(name)
        return default if value is None else value


def active_pack(db: Session) -> ActivePack | None:
    """The enabled pack of highest version, or None when no pack is active."""
    row = (
        db.execute(
            select(ConditionPack)
            .where(ConditionPack.enabled.is_(True))
            .order_by(ConditionPack.version.desc())
        )
        .scalars()
        .first()
    )
    if row is None:
        return None
    return ActivePack(
        pack_key=row.pack_key,
        version=row.version,
        config=dict(row.config or {}),
        awaiting_review=dict(row.awaiting_review or {}),
    )


def pack_is_active(db: Session) -> bool:
    """Whether any pack is active. The settings screen and the engine both ask."""
    return active_pack(db) is not None
