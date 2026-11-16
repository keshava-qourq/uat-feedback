"""Admin configuration routes.

`GET /api/admin/settings` reports whether the two pieces of deployment
configuration this service needs are in place -- the database connection
(`DATABASE_URL`) and the hosted language-model credential
(`ANTHROPIC_API_KEY`) -- as a status string and nothing else. No credential
value is ever read into the response, logged, or written anywhere (NFR-011);
both are read from the environment only.
"""

from __future__ import annotations

import os
from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import require_api_access
from app.database import get_db
from app.dataset import active_dataset_version
from app.services import configured_services, database_reachable

router = APIRouter(
    prefix="/api/admin",
    tags=["admin"],
    dependencies=[Depends(require_api_access)],
)

CONNECTED = "connected"
NOT_CONFIGURED = "not-configured"
#: What a credential's value is shown as: never the value itself (NFR-011).
MASKED = "not-shown"


@router.get("/settings")
def settings(db: Annotated[Session, Depends(get_db)]) -> dict[str, Any]:
    """Masked configuration status: never a credential value, only a status."""
    database = CONNECTED if os.getenv("DATABASE_URL") and database_reachable() else NOT_CONFIGURED
    llm_configured = any(
        (os.getenv(name) or "").strip() for name in ("ANTHROPIC_API_KEY", "LLM_API_KEY")
    )
    llm = CONNECTED if llm_configured else NOT_CONFIGURED
    return {
        "database": {"status": database},
        "llm": {"status": llm},
        "dataset_version": active_dataset_version(db),
        "health": {"status": "ok", "services": configured_services()},
        "credentials": [
            {"name": "database", "status": database, "value": MASKED},
            {"name": "llm", "status": llm, "value": MASKED},
        ],
    }
