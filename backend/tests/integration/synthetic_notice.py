"""Helpers shared by the US-037 synthetic-notice tests (AC-119, AC-120, AC-121).

One definition of "the notice" lives here, so every criterion is measured
against the same words: the notice must say the data is synthetic (100%
synthetic) and that it is not for clinical use.
"""

from __future__ import annotations

import re
from typing import Any

# The two things AC-119 requires the notice to state. Matched case-insensitively
# and tolerant of wording around them, so a banner that says
# "All data is 100% synthetic - not for clinical use" passes.
SYNTHETIC_PATTERN = re.compile(r"synthetic", re.IGNORECASE)
NOT_CLINICAL_PATTERN = re.compile(r"not\s+for\s+clinical\s+use", re.IGNORECASE)


def is_notice(text: str) -> bool:
    """True when `text` states both halves of the synthetic-data notice."""
    return bool(SYNTHETIC_PATTERN.search(text) and NOT_CLINICAL_PATTERN.search(text))


def all_strings(payload: Any) -> list[str]:
    """Every string anywhere in a JSON payload, keys included."""
    found: list[str] = []
    if isinstance(payload, str):
        found.append(payload)
    elif isinstance(payload, dict):
        for key, value in payload.items():
            found.append(str(key))
            found.extend(all_strings(value))
    elif isinstance(payload, list):
        for item in payload:
            found.extend(all_strings(item))
    elif payload is not None:
        found.append(str(payload))
    return found


def payload_carries_notice(payload: Any) -> bool:
    """True when the payload contains the notice in one of its strings."""
    return any(is_notice(text) for text in all_strings(payload))
