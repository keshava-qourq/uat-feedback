"""US-015-1-FIX1: with no Anthropic credential configured the extractor still
reports the clues the active pack's own `match` phrases find in a note, quoting
the sentence verbatim (AC-049) and inventing nothing (AC-050).

Every clue name is read back from the pack, never spelled out here (NFR-019).
"""

from __future__ import annotations

import uuid
from typing import Any

import pytest
from sqlalchemy.orm import Session

from app import clue_extraction
from app.models import Note, Patient

VERSION = "unit-clues-fallback"


def _note(db: Session, text: str) -> Note:
    patient = Patient(
        dataset_patient_id=f"P-{uuid.uuid4().hex[:6]}",
        dataset_version=VERSION,
        display_name="Ada",
    )
    db.add(patient)
    db.commit()
    note = Note(
        patient_id=patient.id,
        source_ref=f"note:{uuid.uuid4().hex[:8]}",
        note_type="imaging_report",
        text=text,
    )
    db.add(note)
    db.commit()
    return note


@pytest.fixture
def clues(db_session: Session) -> dict[str, dict[str, Any]]:
    found = clue_extraction.target_clues(db_session)
    assert found, "the active pack declares no free-text clues"
    return found


def _with_match(clues: dict[str, dict[str, Any]]) -> list[str]:
    return [key for key, definition in clues.items() if definition.get("match_any")]


def _phrases(definition: dict[str, Any]) -> list[str]:
    """The first group of wording the pack declares for this clue."""
    group = list(definition["match_any"])[0]
    return [str(group)] if isinstance(group, str) else [str(term) for term in group]


def test_ac049_without_a_model_the_packs_match_phrases_still_find_a_clue(
    db_session: Session, clues: dict[str, dict[str, Any]]
) -> None:
    declared = _with_match(clues)
    assert declared, "no clue in the active pack declares match phrases"
    key = declared[0]
    phrases = _phrases(clues[key])
    sentence = f"The report states {' and '.join(phrases)} clearly."
    note = _note(db_session, f"Routine study performed. {sentence}")

    found = clue_extraction.extract_from_note(note, clues, client=None)

    assert [f["clue_type"] for f in found] == [key], found
    assert found[0]["quoted_sentence"] == sentence
    assert found[0]["source_ref"] == note.source_ref


def test_ac050_without_a_model_a_clue_free_note_yields_nothing(
    db_session: Session, clues: dict[str, dict[str, Any]]
) -> None:
    note = _note(
        db_session,
        "Attended for a routine medication review. No new concerns were raised today.",
    )

    assert clue_extraction.extract_from_note(note, clues, client=None) == []


def test_ac050_the_fallback_never_quotes_a_sentence_absent_from_the_note(
    db_session: Session, clues: dict[str, dict[str, Any]]
) -> None:
    declared = _with_match(clues)
    phrases = _phrases(clues[declared[0]])
    note = _note(db_session, f"One line only mentioning {' and '.join(phrases)}.")

    for finding in clue_extraction.extract_from_note(note, clues, client=None):
        assert finding["quoted_sentence"] in note.text
