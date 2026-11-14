# Sprint Plan

> Maintained by QuorQ AI SDLC. Text between `sdlc:auto` markers is regenerated; anything outside them is yours and is kept.

<!-- sdlc:auto:start sprints -->
## Sprint 1: Sprint 1

Foundation: deployable app skeleton, dataset ingest into the unified event store, synthetic-data banner

Capacity: 20 points · Committed: 20

| Key | Type | Title | Points | Role | Depends on |
|---|---|---|---|---|---|
| US-001 | Story | Load the supplied dataset files in one admin ingest run | 13 | backend-agent | — |
| ↳ US-001-T1 | Task | Add migrations for the unified event store and ingest run tables | — | backend-agent | — |
| ↳ US-001-T2 | Task | Implement per-file loaders as an RQ worker job | — | backend-agent | — |
| ↳ US-001-T3 | Task | Add ingest run endpoints | — | backend-agent | — |
| ↳ US-001-T4 | Task | Build the admin ingest report screen | — | frontend-agent | — |
| US-037 | Story | Show the synthetic-data banner on every screen | 2 | frontend-agent | US-044 |
| US-044 | Story | Deploy and configure the application as a managed web app | 5 | devops-agent | — |

## Sprint 2: Sprint 2

Provenance on every row, condition pack, clinician sign-in and patient invite generation

Capacity: 20 points · Committed: 19

| Key | Type | Title | Points | Role | Depends on |
|---|---|---|---|---|---|
| US-002 | Story | Keep provenance on every stored fact | 3 | backend-agent | US-001 |
| US-007 | Story | Hold all condition logic in one declarative pack | 8 | backend-agent | — |
| US-026 | Story | Invite a patient to the product | 3 | backend-agent | US-031, US-001 |
| US-031 | Story | Sign in as a clinician with an email and password | 5 | backend-agent | US-044 |

## Sprint 3: Sprint 3

Label quarantine, cutoff-safe inputs, encounter de-duplication, LLM credential configuration

Capacity: 20 points · Committed: 20

| Key | Type | Title | Points | Role | Depends on |
|---|---|---|---|---|---|
| US-003 | Story | Quarantine ground-truth labels away from the engine | 5 | backend-agent | US-001 |
| US-004 | Story | De-duplicate EHR and claim views of the same encounter | 8 | backend-agent | US-001, US-002 |
| US-009 | Story | Score each patient only on data available before their cutoff | 5 | backend-agent | US-002, US-003, US-007 |
| US-017 | Story | Configure the LLM credential as deployment configuration | 2 | devops-agent | US-044 |

## Sprint 4: Sprint 4

Note clue extraction, ASAS/SPARTAN criteria, post-cutoff guardrail

Capacity: 20 points · Committed: 19

| Key | Type | Title | Points | Role | Depends on |
|---|---|---|---|---|---|
| US-010 | Story | Evaluate ASAS referral criteria and SPARTAN points | 8 | backend-agent | US-009, US-007 |
| US-015 | Story | Extract buried clues from notes and imaging reports with a quoted source | 8 | integration-agent | US-002, US-007, US-017 |
| US-034 | Story | Block post-cutoff data from scoring and display | 3 | qa-agent | US-009 |

## Sprint 5: Sprint 5

Counter-evidence caps, tier output with Insufficient history, clinician worklist

Capacity: 20 points · Committed: 18

| Key | Type | Title | Points | Role | Depends on |
|---|---|---|---|---|---|
| US-011 | Story | Cap the tier with counter-evidence and name the alternative | 8 | backend-agent | US-010, US-009, US-015, US-007 |
| US-012 | Story | Output a tier, never a bare score, with an explicit Insufficient history state | 5 | backend-agent | US-010, US-011, US-009 |
| US-018 | Story | Work a worklist sorted by status with the reason and reachable history | 5 | frontend-agent | US-012, US-031 |

## Sprint 6: Sprint 6

One-page case summary, evidence-to-source links, patient invite entry

Capacity: 20 points · Committed: 18

| Key | Type | Title | Points | Role | Depends on |
|---|---|---|---|---|---|
| US-019 | Story | Read a one-page case summary in under two minutes | 8 | frontend-agent | US-010, US-011, US-012 |
| ↳ US-019-T1 | Task | Compose the case payload in GET /api/cases/{patient_id} | — | backend-agent | — |
| ↳ US-019-T2 | Task | Build the one-page case summary layout | — | frontend-agent | — |
| US-020 | Story | Link every evidence item to the source record behind it | 5 | frontend-agent | US-019 |
| US-032 | Story | Enter as a patient through a tokenised invite link | 5 | backend-agent | US-026, US-031 |

## Sprint 7: Sprint 7

Offline training, hybrid live scoring, suggested workup, decision capture

Capacity: 20 points · Committed: 19

| Key | Type | Title | Points | Role | Depends on |
|---|---|---|---|---|---|
| US-013 | Story | Train the model and tune the operating threshold as an offline job | 8 | backend-agent | US-009, US-003, US-010 |
| US-014 | Story | Score live from the persisted artefact combined with the rules layer | 5 | backend-agent | US-013, US-011, US-012 |
| US-021 | Story | See a suggested workup with the reasoning for each item | 3 | backend-agent | US-019, US-010 |
| US-022 | Story | Record a decision with a reason | 3 | backend-agent | US-019, US-031 |

## Sprint 8: Sprint 8

Patient intake, patient timeline, role split enforcement

Capacity: 20 points · Committed: 18

| Key | Type | Title | Points | Role | Depends on |
|---|---|---|---|---|---|
| US-005 | Story | See my records, claims and answers merged into one timeline | 5 | frontend-agent | US-032, US-004, US-009, US-002 |
| US-027 | Story | Complete a symptom intake in about ten minutes | 8 | frontend-agent | US-032, US-007, US-002 |
| ↳ US-027-T1 | Task | Implement intake endpoints with resumable progress | — | backend-agent | — |
| ↳ US-027-T2 | Task | Build one-question-per-screen intake UI | — | frontend-agent | — |
| US-033 | Story | Keep the risk tier on the clinician side only | 5 | security-agent | US-032, US-031, US-005 |

## Sprint 9: Sprint 9

Cited text generation, citation verifier, Insufficient-history detail screen

Capacity: 20 points · Committed: 18

| Key | Type | Title | Points | Role | Depends on |
|---|---|---|---|---|---|
| US-016 | Story | Generate clinician and patient text with a citation on every sentence | 8 | integration-agent | US-019, US-015, US-017, US-010 |
| US-023 | Story | Open the Insufficient-history detail screen with a what-we-still-need list | 5 | frontend-agent | US-012, US-019 |
| US-035 | Story | Block uncited sentences in generated summaries | 5 | backend-agent | US-016 |

## Sprint 10: Sprint 10

Visit prep, share by link/QR, visible gaps, patient-copy guardrail

Capacity: 20 points · Committed: 18

| Key | Type | Title | Points | Role | Depends on |
|---|---|---|---|---|---|
| US-006 | Story | Show the gaps where care was invisible | 5 | frontend-agent | US-005, US-027 |
| US-028 | Story | Get a plain-language visit-prep sheet | 5 | frontend-agent | US-027, US-016, US-005, US-035 |
| US-029 | Story | Share my case with a clinician by link or QR code | 5 | frontend-agent | US-028, US-031, US-019 |
| US-036 | Story | Keep diagnosis names and risk scores out of patient-facing copy | 3 | qa-agent | US-028, US-007, US-016 |

## Sprint 11: Sprint 11

In-app evaluation report, demo persona picker, 60-second performance path, responsive polish

Capacity: 20 points · Committed: 17

| Key | Type | Title | Points | Role | Depends on |
|---|---|---|---|---|---|
| US-038 | Story | Pick a hero persona to drive the demo | 3 | frontend-agent | US-019, US-005, US-001 |
| US-039 | Story | Render a persona from selection to case summary in under sixty seconds | 3 | backend-agent | US-038, US-019, US-016 |
| US-042 | Story | Compute the PRD success metrics inside the product | 8 | backend-agent | US-013, US-014, US-012, US-003 |
| ↳ US-042-T1 | Task | Implement the evaluation job in the worker | — | backend-agent | — |
| ↳ US-042-T2 | Task | Add evaluation endpoints with role enforcement | — | backend-agent | — |
| ↳ US-042-T3 | Task | Build the evaluation report screen | — | frontend-agent | — |
| US-043 | Story | Use the same application on a phone or a desktop | 3 | frontend-agent | US-005, US-018, US-019 |

## Sprint 12: Sprint 12

Odyssey replay, referral packet, workup outcomes and post-workup patient update

Capacity: 20 points · Committed: 18

| Key | Type | Title | Points | Role | Depends on |
|---|---|---|---|---|---|
| US-024 | Story | Export a referral packet as a printable summary | 5 | backend-agent | US-019, US-021, US-009, US-020 |
| US-025 | Story | Record a workup outcome and lower the tier | 5 | backend-agent | US-021, US-019, US-012 |
| US-030 | Story | Receive a clear update after the tests come back | 3 | backend-agent | US-025, US-005 |
| US-040 | Story | Watch the odyssey replay with the lead time | 5 | frontend-agent | US-038, US-012 |

## Sprint 13: Sprint 13

Persona acceptance suite and editable code lists

Capacity: 20 points · Committed: 10

| Key | Type | Title | Points | Role | Depends on |
|---|---|---|---|---|---|
| US-008 | Story | Edit the code lists as pack configuration | 5 | backend-agent | US-007, US-031, US-009 |
| US-041 | Story | Hold the six persona pass tests as an automated acceptance suite | 5 | qa-agent | US-038, US-011, US-012, US-023, US-027, US-016 |

## Unscheduled

_Nothing unscheduled._
<!-- sdlc:auto:end sprints -->
