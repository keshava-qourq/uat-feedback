"""Free-text clue extraction over notes and imaging reports (US-015-1).

The clues this looks for are read from the active condition pack's
`free_text_clues` section (NFR-019): nothing here names a clue, a wording or
a condition. For each note the Anthropic client (`app.llm`) is asked for the
clues present, and every candidate it answers with is verified against the
note before anything is stored:

* its `clue_type` must be one the pack declares;
* its `quoted_sentence` must appear in the note text verbatim -- a sentence
  the model paraphrased or invented is dropped, never persisted;
* its `finding_value`, when the pack declares a closed set for that clue,
  must be one of those values.

A note that yields nothing writes no finding and is still recorded as
processed (`notes.processed_at`), so the cohort run can tell "looked at and
found nothing" from "not looked at yet" (AC-050).

Running twice is safe: a note's prior findings are replaced by the run's own,
so a second pass over the same cohort leaves the same rows.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app import llm
from app.database import SessionLocal
from app.engine.criteria import pack_config
from app.models import Note, NoteFinding

__all__ = [
    "CLUE_SECTION",
    "extract_cohort",
    "extract_from_note",
    "process_note",
    "run_clue_extraction",
    "target_clues",
]

#: The pack section declaring what the extractor looks for.
CLUE_SECTION = "free_text_clues"

#: The answer budget for one note's extraction call.
MAX_TOKENS = 1024


def target_clues(db: Session) -> dict[str, dict[str, Any]]:
    """The clue definitions the active pack declares, keyed by clue type.

    `pack_config` already supplies any section a stored pack row predates
    from the shipped pack file, so this reads one place only.
    """
    section = (pack_config(db) or {}).get(CLUE_SECTION)
    if not isinstance(section, dict):
        return {}
    return {str(key): dict(value or {}) for key, value in section.items()}


def _prompt(text: str, clues: dict[str, dict[str, Any]]) -> str:
    lines = [
        "Read the clinical note below and report only the clues listed that are",
        "actually stated in it. For each one, quote the sentence from the note",
        "exactly, character for character. Invent nothing: if a clue is not in",
        "the note, leave it out entirely.",
        "",
        "Clues:",
    ]
    for key, definition in clues.items():
        described = definition.get("description") or definition.get("label") or key
        values = definition.get("values")
        allowed = f" Allowed values: {', '.join(str(v) for v in values)}." if values else ""
        lines.append(f"- {key}: {described}{allowed}")
    lines += [
        "",
        'Answer with JSON only: {"findings": [{"clue_type": ..., '
        '"finding_value": ..., "quoted_sentence": ...}]}.',
        "",
        "NOTE:",
        text,
    ]
    return "\n".join(lines)


def _answer_text(response: Any) -> str:
    """The text of an Anthropic messages response, whatever shape it arrives in."""
    content = getattr(response, "content", None)
    if content is None and isinstance(response, dict):
        content = response.get("content")
    if isinstance(content, str):
        return content
    parts: list[str] = []
    for block in content or []:
        value = getattr(block, "text", None)
        if value is None and isinstance(block, dict):
            value = block.get("text")
        if value:
            parts.append(str(value))
    return "".join(parts)


def _parse(answer: str) -> list[dict[str, Any]]:
    """The findings list in the model's answer, or nothing when it is unusable."""
    text = answer.strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        return []
    try:
        payload = json.loads(text[start : end + 1])
    except ValueError:
        return []
    found = payload.get("findings") if isinstance(payload, dict) else None
    return [item for item in found or [] if isinstance(item, dict)]


def _verify(
    candidate: dict[str, Any], note_text: str, clues: dict[str, dict[str, Any]]
) -> dict[str, Any] | None:
    """One candidate, kept only when the note really supports it."""
    clue_type = str(candidate.get("clue_type") or "").strip()
    definition = clues.get(clue_type)
    if definition is None:
        return None
    sentence = str(candidate.get("quoted_sentence") or "").strip()
    if not sentence or sentence not in note_text:
        return None
    value = candidate.get("finding_value")
    value = None if value is None else str(value).strip() or None
    allowed = definition.get("values")
    if allowed and value not in {str(item) for item in allowed}:
        return None
    return {"clue_type": clue_type, "finding_value": value, "quoted_sentence": sentence}


def _sentences(text: str) -> list[str]:
    """The note's sentences, each as it stands in the text."""
    found: list[str] = []
    start = 0
    for index, char in enumerate(text):
        if char in ".!?":
            sentence = text[start : index + 1].strip()
            if sentence:
                found.append(sentence)
            start = index + 1
    tail = text[start:].strip()
    if tail:
        found.append(tail)
    return found


def _group_matches(groups: Any, sentence: str) -> bool:
    """True when one group of terms is wholly present in this sentence."""
    for group in groups or []:
        terms = [group] if isinstance(group, str) else list(group or [])
        if terms and all(str(term).lower() in sentence for term in terms):
            return True
    return False


def _fallback(note_text: str, clues: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """The deterministic reading used when no language model is configured.

    The wording it matches comes from the pack (`match_any`, `value_terms`),
    so nothing here names a clue. It quotes whole sentences of the note, so a
    finding is still the exact sentence it came from (AC-049), and a clue the
    note does not state yields nothing (AC-050).
    """
    findings: list[dict[str, Any]] = []
    for clue_type, definition in clues.items():
        groups = definition.get("match_any")
        if not groups:
            continue
        for sentence in _sentences(note_text):
            lowered = sentence.lower()
            if not _group_matches(groups, lowered):
                continue
            value = None
            value_terms = definition.get("value_terms")
            if isinstance(value_terms, dict):
                for candidate, candidate_groups in value_terms.items():
                    if _group_matches(candidate_groups, lowered):
                        value = str(candidate)
                        break
                if value is None:
                    break
            findings.append(
                {
                    "clue_type": clue_type,
                    "finding_value": value,
                    "quoted_sentence": sentence,
                }
            )
            break
    return findings


def extract_from_note(
    note: Note, clues: dict[str, dict[str, Any]], client: Any | None = None
) -> list[dict[str, Any]]:
    """The verified findings in one note: one entry per target clue found.

    Each entry carries the exact quoted sentence and the note's `source_ref`
    (AC-049). Nothing the note does not contain is ever returned (AC-050).
    """
    if not clues:
        return []
    client = client if client is not None else llm.get_client()
    candidates: list[dict[str, Any]]
    if client is None:
        candidates = _fallback(note.text, clues)
    else:
        try:
            response = client.messages.create(
                model=llm.model_name(),
                max_tokens=MAX_TOKENS,
                messages=[{"role": "user", "content": _prompt(note.text, clues)}],
            )
        except Exception:  # noqa: BLE001 -- a failed call falls back, never crashes
            candidates = _fallback(note.text, clues)
        else:
            candidates = _parse(_answer_text(response))
    findings: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for candidate in candidates:
        verified = _verify(candidate, note.text, clues)
        if verified is None:
            continue
        key = (verified["clue_type"], verified["quoted_sentence"])
        if key in seen:
            continue
        seen.add(key)
        findings.append({**verified, "source_ref": note.source_ref, "note_id": note.id})
    return findings


def process_note(
    db: Session,
    note: Note,
    clues: dict[str, dict[str, Any]],
    client: Any | None = None,
) -> list[dict[str, Any]]:
    """Extract one note, persist its findings and record it as processed.

    Replaces whatever a previous run stored for this note, so re-running is
    safe and never doubles a finding.
    """
    findings = extract_from_note(note, clues, client)
    db.execute(delete(NoteFinding).where(NoteFinding.note_id == note.id))
    model = llm.model_name()
    now = datetime.now(UTC)
    for finding in findings:
        db.add(
            NoteFinding(
                note_id=note.id,
                patient_id=note.patient_id,
                clue_type=finding["clue_type"],
                finding_value=finding["finding_value"],
                quoted_sentence=finding["quoted_sentence"],
                source_ref=finding["source_ref"],
                extractor_model=model,
                extracted_at=now,
            )
        )
    # Recorded as processed whether or not it yielded anything (AC-050).
    note.processed_at = now
    db.commit()
    return findings


def extract_cohort(db: Session, progress: Any = None, client: Any | None = None) -> dict[str, Any]:
    """Run the extractor over every loaded note. Returns the run's counts."""
    clues = target_clues(db)
    notes = list(db.execute(select(Note).order_by(Note.id)).scalars())
    report = {
        "notes_processed": 0,
        "findings": 0,
        "clue_types": sorted(clues),
        "extractor_model": llm.model_name(),
    }
    total = len(notes) or 1
    for done, note in enumerate(notes, start=1):
        report["findings"] += len(process_note(db, note, clues, client))
        report["notes_processed"] += 1
        if progress is not None:
            progress(round(done * 100 / total, 2))
    return report


def run_clue_extraction() -> dict[str, Any]:
    """The RQ job: extract over the cohort, reporting progress on the job meta."""
    try:
        from rq import get_current_job

        job = get_current_job()
    except Exception:  # noqa: BLE001 -- run outside a worker, there is no job meta
        job = None

    def report_progress(pct: float) -> None:
        if job is None:
            return
        job.meta["progress_pct"] = pct
        job.meta["progress_message"] = f"clue extraction {pct}% complete"
        job.save_meta()

    report_progress(0.0)
    db = SessionLocal()
    try:
        result = extract_cohort(db, progress=report_progress)
    finally:
        db.close()
    report_progress(100.0)
    return result
