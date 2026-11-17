"""The condition pack as administrator-editable configuration (AC-020, NFR-019).

`GET /api/admin/pack` hands the whole active pack back as data; `PUT` replaces
it with a full body, validates it against the pack schema and stores it as a
new version, so the next read -- and the next scoring run, which resolves the
pack through `app.pack.active_pack` -- sees the new values with no code
deployment.

Nothing here names a condition, a code, a marker or a rule: the router only
moves the pack's data in and out.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import require_admin
from app.database import get_db
from app.models import ConditionPack, PackChangeLog, User
from app.pack import registry
from app.pack.loader import active_pack

router = APIRouter(prefix="/api/admin", tags=["admin"])

NO_PACK: dict[str, Any] = {
    "pack_key": None,
    "enabled": False,
    "version": None,
    "config": None,
    "awaiting_review": None,
    "updated_by": None,
    "updated_at": None,
    "source": None,
}


class PackBody(BaseModel):
    """A full replacement pack: its declarative content, and why it changed."""

    config: dict[str, Any]
    change_summary: Any | None = None


def _shipped_pack() -> registry.Pack | None:
    """The pack file this deployment ships, or None when packs are switched off.

    With no pack key configured and exactly one pack file present, that file is
    the pack: a deployment does not have to name what it ships only one of.
    """
    if not registry.pack_enabled():
        return None
    key = registry.active_pack_key()
    if key is None:
        keys = registry.list_packs()
        if len(keys) != 1:
            return None
        key = keys[0]
    try:
        return registry.load_pack(key)
    except registry.PackValidationError:
        return None


def _body(db: Session) -> dict[str, Any]:
    """The active pack as configuration data, or the no-pack answer."""
    if not registry.pack_enabled():
        return dict(NO_PACK)
    stored = active_pack(db)
    if stored is not None:
        row = (
            db.execute(
                select(ConditionPack)
                .where(ConditionPack.pack_key == stored.pack_key)
                .where(ConditionPack.version == stored.version)
            )
            .scalars()
            .first()
        )
        return {
            "pack_key": stored.pack_key,
            "enabled": True,
            "version": stored.version,
            "config": stored.config,
            "awaiting_review": stored.awaiting_review,
            "updated_by": row.updated_by if row else None,
            "updated_at": row.updated_at.isoformat() if row and row.updated_at else None,
            "source": "database",
        }
    shipped = _shipped_pack()
    if shipped is None:
        return dict(NO_PACK)
    return {
        "pack_key": shipped.key,
        "enabled": True,
        "version": shipped.version,
        "config": shipped.data,
        "awaiting_review": None,
        "updated_by": None,
        "updated_at": None,
        "source": "file",
    }


def _validation_error(key: str, problem: str) -> HTTPException:
    """FastAPI's validation body, naming the offending key of the pack."""
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=[
            {
                "type": "value_error",
                "loc": ["body", "config", *key.split(".")],
                "msg": f"{key}: {problem}",
            }
        ],
    )


@router.get("/pack")
def get_pack(
    db: Annotated[Session, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
) -> dict[str, Any]:
    """The active pack's full declarative content, or the no-pack answer."""
    return _body(db)


@router.put("/pack")
def put_pack(
    payload: PackBody,
    db: Annotated[Session, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
) -> dict[str, Any]:
    """Replace the pack wholesale; the new values take effect on the next read."""
    try:
        registry.validate(payload.config)
    except registry.PackValidationError as exc:
        raise _validation_error(exc.key, exc.problem) from exc

    pack_key = str(payload.config["pack_key"])
    highest = (
        db.execute(
            select(ConditionPack.version)
            .where(ConditionPack.pack_key == pack_key)
            .order_by(ConditionPack.version.desc())
        )
        .scalars()
        .first()
    )
    version = max(int(highest or 0), int(payload.config["version"])) + 1
    row = ConditionPack(
        pack_key=pack_key,
        version=version,
        enabled=True,
        config=payload.config,
        awaiting_review=None,
        updated_by=admin.email,
        updated_at=datetime.now(UTC),
    )
    db.add(row)
    db.flush()
    db.add(
        PackChangeLog(
            pack_id=row.id,
            changed_by=admin.email,
            changed_at=datetime.now(UTC),
            change_summary={"summary": payload.change_summary, "version": version},
        )
    )
    db.commit()
    # Drop the file-pack cache so a running process re-reads configuration
    # rather than serving what it parsed at startup (NFR-019).
    registry.reload()
    return _body(db)
