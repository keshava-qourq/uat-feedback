"""Extracted findings as evidence, and the admin extraction report (US-015-2).

Two reads sit here, both over the rows `app.clue_extraction` wrote:

* `finding_evidence` turns a patient's stored findings into evidence items.
  Each carries the sentence the extractor quoted and a link back to the full
  note, resolved through `app.provenance.resolve_source_ref` -- the note text
  itself is never copied into the finding, only pointed at (AC-051). Only
  findings whose note is pre-cutoff are returned, so an evidence item can
  never reintroduce something the leakage guarantee hides (NFR-013).
* `extraction_report` totals the run for the admin screen: how many notes
  were processed, how many findings per clue type, the dataset version, and
  the caveat that this dataset's templated note text makes extraction easier
  here than it would be on real clinical text (AC-052). The caveat wording is
  read from the active pack's copy when the pack carries one (NFR-019).
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.clue_extraction import target_clues
from app.dataset import active_dataset_version
from app.engine.inputs import cutoff_date, is_pre_cutoff
from app.models import Note, NoteFinding
from app.provenance import resolve_source_ref

__all__ = ["CAVEAT_COPY_KEY", "DEFAULT_CAVEAT", "caveat", "extraction_report", "finding_evidence"]

#: The pack's copy key carrying this wording, when the pack states it.
CAVEAT_COPY_KEY = "extraction_caveat"

#: Used only when no pack is active or the pack states no wording of its own.
DEFAULT_CAVEAT = (
    "The notes in this dataset are generated from templates, which makes clue "
    "extraction easier here than it would be on real clinical text."
)


def note_link(patient_id: str, source_ref: str) -> str:
    """The API path that serves the full note behind a finding."""
    return f"/api/cases/{patient_id}/notes/{source_ref}"


def finding_evidence(db: Session, patient_id: str) -> list[dict[str, Any]]:
    """One evidence item per extracted finding of this patient (AC-051)."""
    cutoff = cutoff_date(db, patient_id)
    rows = list(
        db.execute(
            select(NoteFinding)
            .where(NoteFinding.patient_id == patient_id)
            .order_by(NoteFinding.clue_type)
        ).scalars()
    )
    items: list[dict[str, Any]] = []
    for row in rows:
        record = resolve_source_ref(db, row.source_ref, patient_id)
        if not is_pre_cutoff(record.note_time, cutoff):
            continue
        items.append(
            {
                "note_finding_id": row.id,
                "clue_type": row.clue_type,
                "finding_value": row.finding_value,
                # The sentence as it stands in the note, never a paraphrase.
                "quoted_sentence": row.quoted_sentence,
                "source_ref": row.source_ref,
                "source_tag": "note",
                # Resolved through provenance: the note is pointed at, its
                # text is not copied into the finding.
                "note_link": note_link(patient_id, row.source_ref),
                "note_found": record.found,
                "note_type": record.note_type,
                "note_time": record.note_time.isoformat() if record.note_time else None,
            }
        )
    return items


def caveat(db: Session) -> str:
    """The templated-text caveat: the pack's wording when it states one."""
    from app.engine.criteria import pack_config

    config = pack_config(db) or {}
    copy = config.get("copy")
    stated = copy.get(CAVEAT_COPY_KEY) if isinstance(copy, dict) else None
    return str(stated).strip() if isinstance(stated, str) and stated.strip() else DEFAULT_CAVEAT


def _counts(db: Session) -> dict[str, int]:
    """Findings per clue type: every clue the pack declares, plus any stored."""
    counts = {clue: 0 for clue in target_clues(db)}
    rows = db.execute(
        select(NoteFinding.clue_type, func.count(NoteFinding.id)).group_by(NoteFinding.clue_type)
    ).all()
    for clue_type, count in rows:
        counts[str(clue_type)] = int(count)
    return counts


def extraction_report(db: Session) -> dict[str, Any]:
    """The body of `GET /api/admin/extraction-report` (AC-052)."""
    processed = (
        db.execute(
            select(func.count(Note.id)).where(Note.processed_at.is_not(None))
        ).scalar_one_or_none()
        or 0
    )
    counts = _counts(db)
    return {
        "dataset_version": active_dataset_version(db),
        "notes_processed": int(processed),
        "findings_by_clue_type": [
            {"clue_type": clue, "count": count} for clue, count in sorted(counts.items())
        ],
        # The same counts keyed by clue type, for a screen reading them directly.
        "findings_by_clue": dict(sorted(counts.items())),
        "findings_total": sum(counts.values()),
        "caveat": caveat(db),
    }
