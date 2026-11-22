"""The evaluation-only label store (US-003, AC-008/009/010).

`labels.csv` carries ground truth -- archetype, typicality, clue_density,
hla_b27_true and the axSpA label -- beside two columns the running
application legitimately needs: `eval_cutoff_date` and `split`.

This module is the *only* place in the codebase that touches the
`patient_labels` table. Operational readers (the engine, the routers, the
demo) call `operational_labels`, which returns exactly the two permitted
fields; the allowlist is the module-level constant `OPERATIONAL_FIELDS` and is
enforced here in code, so asking for any other field raises `LeakageError`
rather than relying on a caller's convention (AC-010).

`evaluation_labels` is the evaluation-only accessor (AC-009): it returns the
ground-truth columns and may be called by the cohort evaluation report alone
-- never by an engine, router or timeline module, where its values would
become a leaked input (NFR-013).
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from sqlalchemy import Boolean, Date, ForeignKey, Numeric, String, delete, insert, select
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

__all__ = [
    "EVALUATION_FIELDS",
    "OPERATIONAL_FIELDS",
    "LeakageError",
    "PatientLabel",
    "evaluation_labels",
    "insert_labels",
    "operational_field",
    "operational_labels",
    "purge",
]

#: The only fields an operational reader may ever see from this store.
OPERATIONAL_FIELDS: tuple[str, ...] = ("eval_cutoff_date", "split")

#: Ground truth: reachable through `evaluation_labels` and nothing else.
EVALUATION_FIELDS: tuple[str, ...] = (
    "archetype",
    "typicality",
    "clue_density",
    "hla_b27_true",
    "axspa_label",
)


class LeakageError(ValueError):
    """An operational reader asked the label store for a ground-truth field."""


class PatientLabel(Base):
    """One row of labels.csv, held apart from everything scoring may read."""

    __tablename__ = "patient_labels"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id: Mapped[str] = mapped_column(
        String, ForeignKey("patients.id"), nullable=False, index=True
    )
    dataset_version: Mapped[str] = mapped_column(String, nullable=False)
    split: Mapped[str] = mapped_column(String, nullable=False)
    #: A plain date, with no time-of-day or zone: every cutoff comparison is
    #: made against the UTC calendar date.
    eval_cutoff_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    archetype: Mapped[str | None] = mapped_column(String, nullable=True)
    typicality: Mapped[str | None] = mapped_column(String, nullable=True)
    clue_density: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    hla_b27_true: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    axspa_label: Mapped[bool | None] = mapped_column(Boolean, nullable=True)


def operational_labels(
    db, patient_id: str, fields: tuple[str, ...] = OPERATIONAL_FIELDS
) -> dict[str, Any]:
    """The permitted operational view of a patient's labels, and nothing else.

    Returns exactly `{'eval_cutoff_date': date|None, 'split': str}`. Asking
    for any other field raises `LeakageError` (AC-010).
    """
    for field in fields:
        if field not in OPERATIONAL_FIELDS:
            raise LeakageError(
                f"'{field}' is not an operational label field; only "
                f"{', '.join(OPERATIONAL_FIELDS)} may be read operationally"
            )
    row = (
        db.execute(select(PatientLabel).where(PatientLabel.patient_id == patient_id))
        .scalars()
        .first()
    )
    return {
        "eval_cutoff_date": row.eval_cutoff_date if row is not None else None,
        "split": row.split if row is not None else "",
    }


def operational_field(field: str, db=None, patient_id: str | None = None) -> Any:
    """One operational label field, refused unless it is on the allowlist (AC-010).

    Raises `LeakageError` for any ground-truth field. With no session and
    patient given there is nothing to read, so `LookupError` is raised.
    """
    if field not in OPERATIONAL_FIELDS:
        raise LeakageError(
            f"'{field}' is not an operational label field; only "
            f"{', '.join(OPERATIONAL_FIELDS)} may be read operationally"
        )
    if db is None or patient_id is None:
        raise LookupError(f"no label row is loaded, so '{field}' cannot be read")
    return operational_labels(db, patient_id)[field]


def evaluation_labels(db, patient_id: str | None = None) -> list[dict[str, Any]]:
    """EVALUATION ONLY (AC-009): the ground-truth columns of the label store.

    The cohort evaluation report is the only component permitted to call this.
    No engine, router or timeline module may import it: a value it returns may
    not reach a score, a feature or a rendered payload (NFR-013).
    """
    query = select(PatientLabel)
    if patient_id is not None:
        query = query.where(PatientLabel.patient_id == patient_id)
    return [
        {
            "patient_id": row.patient_id,
            "split": row.split,
            "eval_cutoff_date": row.eval_cutoff_date,
            **{field: getattr(row, field) for field in EVALUATION_FIELDS},
        }
        for row in db.execute(query).scalars().all()
    ]


def insert_labels(db, mappings: list[dict[str, Any]]) -> None:
    """Bulk-insert label rows. The ingest job is the only caller."""
    if mappings:
        db.execute(insert(PatientLabel), mappings)


def purge(db, dataset_version: str) -> None:
    """Drop the prior labels load of this dataset version, so a re-run replaces it."""
    db.execute(delete(PatientLabel).where(PatientLabel.dataset_version == dataset_version))
