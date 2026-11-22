# Development

> Maintained by QuorQ AI SDLC. Text between `sdlc:auto` markers is regenerated; anything outside them is yours and is kept.

<!-- sdlc:auto:start narrative -->
### DEV-US-003 · approved · source: dev:US-003

Ticket US-003, "Quarantine ground-truth labels away from the engine", was delivered during the development run. The work is attributed to commit 63bcdd7c77b4eda58477e702a743a91bc1eea514. No further implementation detail was provided in the input.

- Ticket: US-003 — Quarantine ground-truth labels away from the engine
- Status reported by the development run: delivered
- Commit: 63bcdd7c77b4eda58477e702a743a91bc1eea514
- The same commit hash is also recorded against ticket US-009; the input does not explain whether this is a shared commit or a recording discrepancy. Both attributions are retained as given.
- Not stated in the input: date, author/reviewer, files or modules changed, tests run, acceptance evidence.

**Related:** US-003

### DEV-US-004 · approved · source: dev:US-004

Ticket US-004, "De-duplicate EHR and claim views of the same encounter", was delivered during the development run. The work is attributed to commit 0b7afaa3940760d9f6bfdaaea9be5523456ffe09. No further implementation detail was provided in the input.

- Ticket: US-004 — De-duplicate EHR and claim views of the same encounter
- Status reported by the development run: delivered
- Commit: 0b7afaa3940760d9f6bfdaaea9be5523456ffe09
- Not stated in the input: date, author/reviewer, de-duplication rule or matching keys used, data volumes affected, tests run, acceptance evidence.

**Related:** US-004

### DEV-US-009 · approved · source: dev:US-009

Ticket US-009, "Score each patient only on data available before their cutoff", was delivered during the development run. The work is attributed to commit 63bcdd7c77b4eda58477e702a743a91bc1eea514. No further implementation detail was provided in the input.

- Ticket: US-009 — Score each patient only on data available before their cutoff
- Status reported by the development run: delivered
- Commit: 63bcdd7c77b4eda58477e702a743a91bc1eea514
- The same commit hash is also recorded against ticket US-003; the input does not explain whether the two tickets were landed together in one commit or whether one attribution is in error. Both attributions are recorded as given.
- Not stated in the input: date, author/reviewer, how the cutoff is defined or enforced, tests run, acceptance evidence.

**Related:** US-009

### DEV-US-017 · approved · source: dev:US-017

Ticket US-017, "Configure the LLM credential as deployment configuration", was delivered during the development run. The work is attributed to commit 2120acc390cc75268ca0a9206a10b835879d3465. No further implementation detail was provided in the input.

- Ticket: US-017 — Configure the LLM credential as deployment configuration
- Status reported by the development run: delivered
- Commit: 2120acc390cc75268ca0a9206a10b835879d3465
- The credential itself is supplied at deploy time as configuration (e.g. <llm-api-key>) and is not recorded in this document or in source control.
- Not stated in the input: date, author/reviewer, configuration mechanism (environment variable, secret store, config file), rotation handling, tests run, acceptance evidence.

**Related:** US-017

### DEV-US-FIX-1 · draft · source: dev:US-FIX-1

Ticket US-FIX-1, "Fix the scaffold's failing checks", is reported as failed. No commit was produced. The input gives no diagnosis, error output, or remediation plan, so the cause and current state of the scaffold's checks remain undocumented.

- Ticket: US-FIX-1 — Fix the scaffold's failing checks
- Status reported by the development run: failed
- Commit: none
- Open point for follow-up: the scaffold's checks were not reported as fixed; the input does not say which checks fail, why the attempt failed, or whether it blocks the delivered tickets.
- Not stated in the input: date, author, error logs, retry attempts, owner for remediation.
- No requirement key was given for this ticket in the input, so related_ids is left empty rather than guessed.
<!-- sdlc:auto:end narrative -->
