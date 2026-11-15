"""The one wording of the synthetic-data notice (US-037, AC-119/120/121).

Every payload a screen renders and every page of every export carries this
string, so the guardrail measures one sentence rather than a dozen variants.
Plain ASCII on purpose: the PDF exports draw it with a base-14 font.
"""

SYNTHETIC_DATA_NOTICE = "All data shown is 100% synthetic - not for clinical use."


def with_notice(payload: dict) -> dict:
    """The payload as returned to a screen, with the notice alongside it."""
    return {"notice": SYNTHETIC_DATA_NOTICE, **payload}
