"""The tier vocabulary, spelled once.

The engine's output is a tier, never a bare score, and the worklist orders by
High, Moderate, Insufficient history, Low -- not alphabetically and not by the
score behind it. Both the engine and the API read these names, so a typo
cannot produce a tier no screen matches.

"Insufficient history" is a tier in its own right, not a missing value: the
product's whole point is saying "we cannot tell, and here is what is missing"
rather than quietly scoring Low.
"""

from __future__ import annotations

TIER_HIGH = "High"
TIER_MODERATE = "Moderate"
TIER_INSUFFICIENT_HISTORY = "Insufficient history"
TIER_LOW = "Low"

#: Every tier the engine may emit.
TIERS: tuple[str, ...] = (TIER_HIGH, TIER_MODERATE, TIER_INSUFFICIENT_HISTORY, TIER_LOW)

#: The clinician worklist's order, per the API spec for `GET /api/worklist`.
WORKLIST_ORDER: tuple[str, ...] = (
    TIER_HIGH,
    TIER_MODERATE,
    TIER_INSUFFICIENT_HISTORY,
    TIER_LOW,
)


def worklist_rank(tier: str | None) -> int:
    """Sort key for a tier in the worklist. An unknown tier sorts last."""
    try:
        return WORKLIST_ORDER.index(tier or "")
    except ValueError:
        return len(WORKLIST_ORDER)
