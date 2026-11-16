"""What every guardrail check answers with.

One shape for all four, so the cohort suite can sum violations across them and
report "0" or name exactly what failed, and so a request-time validator and a
build-time sweep never diverge on what counts as a violation.

A result is `ok` when it has no violations: a guardrail that could not run is
not a pass, so a check that cannot evaluate reports a violation saying so
rather than returning an empty result.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class GuardrailViolation:
    """One thing a guardrail refused, named well enough to fix it.

    `guardrail` is the check's key ("post_cutoff", "citation", "patient_copy",
    "synthetic_notice"); `where` locates it (a route, a patient id, a sentence
    index); `detail` says what was wrong in plain words. No violation ever
    carries a credential or a whole patient payload -- it is read in a build
    log.
    """

    guardrail: str
    where: str
    detail: str


@dataclass(frozen=True)
class GuardrailResult:
    """The outcome of one guardrail over one subject (a payload, a patient, a route)."""

    guardrail: str
    violations: tuple[GuardrailViolation, ...] = field(default=())

    @property
    def ok(self) -> bool:
        """True only when nothing was refused."""
        return not self.violations

    @property
    def count(self) -> int:
        return len(self.violations)

    def with_violation(self, where: str, detail: str) -> GuardrailResult:
        """This result plus one more violation."""
        return GuardrailResult(
            guardrail=self.guardrail,
            violations=(
                *self.violations,
                GuardrailViolation(guardrail=self.guardrail, where=where, detail=detail),
            ),
        )

    @staticmethod
    def passing(guardrail: str) -> GuardrailResult:
        """A clean result for `guardrail`."""
        return GuardrailResult(guardrail=guardrail)
