"""The four shipped guardrails, as a package the API and the test suite share.

The architecture names them explicitly:

1. **Post-cutoff filter** -- nothing dated on or after a patient's evaluation
   cutoff may reach a scoring input or a rendered payload.
2. **Citation verifier** -- a generated sentence whose citation does not
   resolve to an existing record for that patient is blocked or flagged.
3. **Patient-facing wording scanner** -- no prohibited term (the pack's list:
   tier names, scores, the condition name) appears in a patient-role string.
4. **Synthetic-data banner** -- the notice is present on every route and on
   every page of every export.

Each runs twice over: as a request-time validator in the API, and as a cohort
suite that fails the build on any non-zero count. The checks themselves belong
to their tickets (US-034 onward). What is fixed here is the shape every one of
them reports in, so the cohort suite can total them without knowing which
guardrail produced which row.
"""

from app.guardrails.result import GuardrailResult, GuardrailViolation

__all__ = ["GuardrailResult", "GuardrailViolation"]
