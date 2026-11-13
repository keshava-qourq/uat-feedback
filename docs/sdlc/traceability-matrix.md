# Traceability Matrix

> Maintained by QuorQ AI SDLC. Text between `sdlc:auto` markers is regenerated; anything outside them is yours and is kept.

<!-- sdlc:auto:start legend -->
Built from recorded links, not written by a model: requirement key → plan item (`source_stable_key`) → development ticket (`stable_key`) → the ticket's test steps → the last live deployment that started after the work finished. **AC tests** counts the story's acceptance criteria that have a test case, and those whose test cases all passed in the latest finished E2E run.
<!-- sdlc:auto:end legend -->

<!-- sdlc:auto:start matrix -->
| Requirement | Epic | Title | Plan items | Sprint | Design | Code | Commits | Ticket | Tests | AC tests | Deployed |
|---|---|---|---|---|---|---|---|---|---|---|---|
| US-001 | EPIC-001 | Load the supplied dataset files in one admin ingest run | — | — | — | — | — | not started | not run | 0/4 tested · 0/4 passing | — |
| US-002 | EPIC-001 | Keep provenance on every stored fact | — | — | — | — | — | not started | not run | 0/3 tested · 0/3 passing | — |
| US-003 | EPIC-001 | Quarantine ground-truth labels away from the engine | — | — | — | — | — | not started | not run | 0/3 tested · 0/3 passing | — |
| US-004 | EPIC-001 | De-duplicate EHR and claim views of the same encounter | — | — | — | — | — | not started | not run | 0/3 tested · 0/3 passing | — |
| US-005 | EPIC-002 | See my records, claims and answers merged into one timeline | — | — | — | — | — | not started | not run | 0/3 tested · 0/3 passing | — |
| US-006 | EPIC-002 | Show the gaps where care was invisible | — | — | — | — | — | not started | not run | 0/3 tested · 0/3 passing | — |
| US-007 | EPIC-003 | Hold all condition logic in one declarative pack | — | — | — | — | — | not started | not run | 0/3 tested · 0/3 passing | — |
| US-008 | EPIC-003 | Edit the code lists as pack configuration | — | — | — | — | — | not started | not run | 0/4 tested · 0/4 passing | — |
| US-009 | EPIC-004 | Score each patient only on data available before their cutoff | — | — | — | — | — | not started | not run | 0/3 tested · 0/3 passing | — |
| US-010 | EPIC-004 | Evaluate ASAS referral criteria and SPARTAN points | — | — | — | — | — | not started | not run | 0/3 tested · 0/3 passing | — |
| US-011 | EPIC-004 | Cap the tier with counter-evidence and name the alternative | — | — | — | — | — | not started | not run | 0/4 tested · 0/4 passing | — |
| US-012 | EPIC-004 | Output a tier, never a bare score, with an explicit Insufficient history state | — | — | — | — | — | not started | not run | 0/4 tested · 0/4 passing | — |
| US-013 | EPIC-005 | Train the model and tune the operating threshold as an offline job | — | — | — | — | — | not started | not run | 0/4 tested · 0/4 passing | — |
| US-014 | EPIC-005 | Score live from the persisted artefact combined with the rules layer | — | — | — | — | — | not started | not run | 0/4 tested · 0/4 passing | — |
| US-015 | EPIC-006 | Extract buried clues from notes and imaging reports with a quoted source | — | — | — | — | — | not started | not run | 0/4 tested · 0/4 passing | — |
| US-016 | EPIC-006 | Generate clinician and patient text with a citation on every sentence | — | — | — | — | — | not started | not run | 0/3 tested · 0/3 passing | — |
| US-017 | EPIC-006 | Configure the LLM credential as deployment configuration | — | — | — | — | — | not started | not run | 0/2 tested · 0/2 passing | — |
| US-018 | EPIC-007 | Work a worklist sorted by status with the reason and reachable history | — | — | — | — | — | not started | not run | 0/4 tested · 0/4 passing | — |
| US-019 | EPIC-007 | Read a one-page case summary in under two minutes | — | — | — | — | — | not started | not run | 0/4 tested · 0/4 passing | — |
| US-020 | EPIC-007 | Link every evidence item to the source record behind it | — | — | — | — | — | not started | not run | 0/3 tested · 0/3 passing | — |
| US-021 | EPIC-007 | See a suggested workup with the reasoning for each item | — | — | — | — | — | not started | not run | 0/3 tested · 0/3 passing | — |
| US-022 | EPIC-007 | Record a decision with a reason | — | — | — | — | — | not started | not run | 0/3 tested · 0/3 passing | — |
| US-023 | EPIC-007 | Open the Insufficient-history detail screen with a what-we-still-need list | — | — | — | — | — | not started | not run | 0/3 tested · 0/3 passing | — |
| US-024 | EPIC-007 | Export a referral packet as a printable summary | — | — | — | — | — | not started | not run | 0/3 tested · 0/3 passing | — |
| US-025 | EPIC-007 | Record a workup outcome and lower the tier | — | — | — | — | — | not started | not run | 0/3 tested · 0/3 passing | — |
| US-026 | EPIC-007 | Invite a patient to the product | — | — | — | — | — | not started | not run | 0/3 tested · 0/3 passing | — |
| US-027 | EPIC-008 | Complete a symptom intake in about ten minutes | — | — | — | — | — | not started | not run | 0/4 tested · 0/4 passing | — |
| US-028 | EPIC-008 | Get a plain-language visit-prep sheet | — | — | — | — | — | not started | not run | 0/3 tested · 0/3 passing | — |
| US-029 | EPIC-008 | Share my case with a clinician by link or QR code | — | — | — | — | — | not started | not run | 0/3 tested · 0/3 passing | — |
| US-030 | EPIC-008 | Receive a clear update after the tests come back | — | — | — | — | — | not started | not run | 0/3 tested · 0/3 passing | — |
| US-031 | EPIC-009 | Sign in as a clinician with an email and password | — | — | — | — | — | not started | not run | 0/5 tested · 0/5 passing | — |
| US-032 | EPIC-009 | Enter as a patient through a tokenised invite link | — | — | — | — | — | not started | not run | 0/3 tested · 0/3 passing | — |
| US-033 | EPIC-009 | Keep the risk tier on the clinician side only | — | — | — | — | — | not started | not run | 0/4 tested · 0/4 passing | — |
| US-034 | EPIC-010 | Block post-cutoff data from scoring and display | — | — | — | — | — | not started | not run | 0/2 tested · 0/2 passing | — |
| US-035 | EPIC-010 | Block uncited sentences in generated summaries | — | — | — | — | — | not started | not run | 0/3 tested · 0/3 passing | — |
| US-036 | EPIC-010 | Keep diagnosis names and risk scores out of patient-facing copy | — | — | — | — | — | not started | not run | 0/2 tested · 0/2 passing | — |
| US-037 | EPIC-010 | Show the synthetic-data banner on every screen | — | — | — | — | — | not started | not run | 0/3 tested · 0/3 passing | — |
| US-038 | EPIC-011 | Pick a hero persona to drive the demo | — | — | — | — | — | not started | not run | 0/3 tested · 0/3 passing | — |
| US-039 | EPIC-011 | Render a persona from selection to case summary in under sixty seconds | — | — | — | — | — | not started | not run | 0/3 tested · 0/3 passing | — |
| US-040 | EPIC-011 | Watch the odyssey replay with the lead time | — | — | — | — | — | not started | not run | 0/3 tested · 0/3 passing | — |
| US-041 | EPIC-011 | Hold the six persona pass tests as an automated acceptance suite | — | — | — | — | — | not started | not run | 0/5 tested · 0/5 passing | — |
| US-042 | EPIC-012 | Compute the PRD success metrics inside the product | — | — | — | — | — | not started | not run | 0/5 tested · 0/5 passing | — |
| US-043 | EPIC-013 | Use the same application on a phone or a desktop | — | — | — | — | — | not started | not run | 0/3 tested · 0/3 passing | — |
| US-044 | EPIC-013 | Deploy and configure the application as a managed web app | — | — | — | — | — | not started | not run | 0/3 tested · 0/3 passing | — |
<!-- sdlc:auto:end matrix -->
