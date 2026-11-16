"""The dataset version the application is currently serving.

It is the `dataset_version` of the most recent ingest run that passed; until
one has, there is no active dataset and the answer is `None`.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models import IngestRun


def active_dataset_version(db: Session) -> str | None:
    """The latest succeeded ingest run's dataset version, or None."""
    try:
        return (
            db.execute(
                select(IngestRun.dataset_version)
                .where(IngestRun.status == "succeeded")
                .order_by(IngestRun.started_at.desc())
            )
            .scalars()
            .first()
        )
    except SQLAlchemyError:
        # /health must still answer when the database is unreachable.
        db.rollback()
        return None
