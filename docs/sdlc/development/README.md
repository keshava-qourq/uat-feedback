# Development

> Maintained by QuorQ AI SDLC. Text between `sdlc:auto` markers is regenerated; anything outside them is yours and is kept.

<!-- sdlc:auto:start narrative -->
### DEV-US-011 · approved · source: dev:US-011

Ticket US-011, "Cap the tier with counter-evidence and name the alternative", was delivered. It changes how the assessment tier responds when counter-evidence is present, capping the tier and naming an alternative explanation. Delivered in commit 59b86476b5dd220898591dc33f8007d6081841a2.

- Ticket: US-011 — Cap the tier with counter-evidence and name the alternative
- Status: delivered
- Commit: 59b86476b5dd220898591dc33f8007d6081841a2 (shared with US-012 and US-045)
- Scope per ticket title: when counter-evidence exists, the resulting tier is capped, and the alternative explanation is stated explicitly.
- Closely coupled to US-012 (tiered output rather than a bare score); both shipped in the same commit.
- Not stated in the input: implementation detail, author, review/approval, delivery date, or test outcome.

**Related:** US-011, US-012

### DEV-US-012 · approved · source: dev:US-012

Ticket US-012, "Output a tier, never a bare score, with an explicit Insufficient history state", was delivered. The output surface returns a tier rather than a raw numeric score and includes a distinct Insufficient history state. Delivered in commit 59b86476b5dd220898591dc33f8007d6081841a2.

- Ticket: US-012 — Output a tier, never a bare score, with an explicit Insufficient history state
- Status: delivered
- Commit: 59b86476b5dd220898591dc33f8007d6081841a2 (shared with US-011 and US-045)
- Scope per ticket title: results are expressed as a tier; a bare score is never emitted; an explicit "Insufficient history" state is available as a distinct outcome.
- Coupled to US-011, which caps that tier in the presence of counter-evidence.
- Not stated in the input: tier names/thresholds, implementation detail, author, review/approval, delivery date, or test outcome.

**Related:** US-012, US-011

### DEV-US-045 · approved · source: dev:US-045

Ticket US-045, "Remove the sign-in form from the /start entry screen", was delivered. The /start entry screen no longer presents a sign-in form. Delivered in commit 59b86476b5dd220898591dc33f8007d6081841a2.

- Ticket: US-045 — Remove the sign-in form from the /start entry screen
- Status: delivered
- Commit: 59b86476b5dd220898591dc33f8007d6081841a2 (shared with US-011 and US-012)
- Scope per ticket title: the sign-in form is removed from the /start entry screen.
- Not stated in the input: what (if anything) replaces the form, any downstream auth impact, author, review/approval, delivery date, or test outcome.

**Related:** US-045
<!-- sdlc:auto:end narrative -->
