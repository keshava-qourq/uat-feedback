"""The scoring and evidence engine, as a package inside the FastAPI app.

The architecture's `engine` component builds each patient's leakage-safe
pre-cutoff input set, evaluates ASAS criteria and SPARTAN points from the
pack, applies the persisted model artefact and its operating threshold when
one is present (rules-only when it is absent), applies counter-evidence and
demotion rules *after* the model contribution, computes reachable history and
the Insufficient-history state, and assembles evidence for / against /
conflicting with a resolvable source reference on every item.

None of that is written here: each piece is a development ticket (US-005
onward). What this package fixes now is the vocabulary the rest of the app
imports -- the tier names and the one leakage-safety helper -- so no ticket
invents a second spelling of "Insufficient history" or its own cutoff filter.
"""

from app.engine.tiers import (
    TIER_HIGH,
    TIER_INSUFFICIENT_HISTORY,
    TIER_LOW,
    TIER_MODERATE,
    TIERS,
    WORKLIST_ORDER,
    worklist_rank,
)

__all__ = [
    "TIERS",
    "TIER_HIGH",
    "TIER_INSUFFICIENT_HISTORY",
    "TIER_LOW",
    "TIER_MODERATE",
    "WORKLIST_ORDER",
    "worklist_rank",
]
