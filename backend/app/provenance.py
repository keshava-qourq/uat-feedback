"""Resolving an event's `source_ref` back to the record it came from.

Provenance is a property of every stored event: `source_ref` is a working join
key into `notes`, so a screen or an export can show the note text behind an
item rather than asserting it unsourced. A reference that resolves to nothing
is a first-class answer (`found=False`), never an exception -- a dangling
reference must be reported, not crash the read.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Note


@dataclass(frozen=True)
class ProvenanceRecord:
    """What a `source_ref` resolved to, or an explicit not-found."""

    source_ref: str
    found: bool
    note_text: str | None = None
    note_type: str | None = None
    note_time: datetime | None = None

    def __bool__(self) -> bool:
        return self.found


def resolve_source_ref(
    db: Session, source_ref: str, patient_id: str | None = None
) -> ProvenanceRecord:
    """The note `source_ref` points at, or a not-found record.

    `patient_id` scopes the lookup when given, so one patient's reference can
    never resolve into another patient's note.
    """
    reference = (source_ref or "").strip()
    if not reference:
        return ProvenanceRecord(source_ref=source_ref or "", found=False)
    query = select(Note).where(Note.source_ref == reference)
    if patient_id is not None:
        query = query.where(Note.patient_id == patient_id)
    note = db.execute(query).scalars().first()
    if note is None:
        return ProvenanceRecord(source_ref=reference, found=False)
    return ProvenanceRecord(
        source_ref=reference,
        found=True,
        note_text=note.text,
        note_type=note.note_type,
        note_time=note.note_time,
    )
