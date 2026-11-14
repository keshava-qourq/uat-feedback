# Planning

> Maintained by QuorQ AI SDLC. Text between `sdlc:auto` markers is regenerated; anything outside them is yours and is kept.

<!-- sdlc:auto:start narrative -->
### EPIC-001 · approved · source: plan:EPIC-001

Admin-run, load-once ingest of the supplied synthetic dataset v0.1 into a normalised unified-event model with provenance on every row. Ground-truth labels are kept physically apart from anything the engine can read.

- Goal: load patients, labels, events (~572k rows), notes (~40k), intake, coverage, encounter_truth, heroes.json and the FHIR NDJSON files once.
- Assumptions:
  - PostgreSQL holds the loaded dataset. Files are loaded once by an admin step, not parsed per request, so a persona renders inside the 60-second demo budget.
  - The product ingests files and never generates a cohort. The synthetic data generator is out of scope.
  - labels.csv is ground truth for evaluation only and is physically separated from anything the engine can read.
- Plan tasks: migrations for the event store and ingest run tables, per-file loaders as an RQ worker job, ingest run endpoints, admin ingest report screen.
- Story points on stories: 29 (stories only; tasks unpointed).

**Related:** US-001, US-002, US-003, US-004, US-001-T1, US-001-T2, US-001-T3, US-001-T4

### EPIC-002 · approved · source: plan:EPIC-002

One chronological timeline per patient, with every item tagged Record / Insurance claim / You told us. Fragmentation in the data is made visible rather than hidden.

- Goal: show self-paid care, unconnected providers, pre-coverage periods, payer switches and short reachable history.
- Assumption: roughly 32% of true encounters appear in no source, and 6% of patients have only ~10 months reachable. The product states what it cannot see and does not interpolate it.
- Story points on stories: 10.

**Related:** US-005, US-006

### EPIC-003 · approved · source: plan:EPIC-003

All condition-specific logic (code lists, signals, ASAS/SPARTAN criteria, counter-evidence rules, suggested workup, patient copy) sits in one configuration-driven axSpA condition pack. Adding a second condition later should be configuration, not a rewrite.

- Assumptions:
  - Only the axSpA pack ships. A second pack (lupus, endometriosis) is out of scope, so the pack boundary is proven by structure and an automated check, not by a second pack.
  - The clinical advisor is deferred. Code lists, thresholds, counter-evidence rules and patient wording are flagged as awaiting clinical sign-off but do not block the build.
- Story points on stories: 13.

**Related:** US-007, US-008

### EPIC-004 · approved · source: plan:EPIC-004

The explainable half of the engine. It scores each patient strictly as of their eval_cutoff_date, evaluates ASAS referral criteria and SPARTAN points, applies counter-evidence caps, and outputs a tier (High / Moderate / Low / Insufficient history) rather than a bare score.

- Assumption: a plain ASAS/SPARTAN rules layer flags 95% of OCI, 85% of sports and 70% of HLA-B27-positive mechanical look-alikes, against a target of under 10% false-High each. The counter-evidence and demotion rules are therefore load-bearing, and their thresholds are flagged as awaiting clinical sign-off.
- Story points on stories: 26.

**Related:** US-009, US-010, US-011, US-012

### EPIC-005 · approved · source: plan:EPIC-005

The precision half of the engine. An in-system offline job builds features, trains on the train split, tunes the threshold on val and reports test once. It persists a model artefact and threshold that live scoring applies alongside the rules layer.

- Recorded conflict between inputs:
  - Version A (Lightweight MVP baseline): rules-only scoring with an optional dataset-supplied score column.
  - Version B (confirmed understanding): the dataset contains no score column, so the model is trained inside the system.
  - The input states B supersedes A, and the conflict is recorded rather than silently resolved.
- Assumption: training runs as a backend job and is not retrained per request. Clinician feedback does not retrain it in this build.
- Story points on stories: 13.

**Related:** US-013, US-014

### EPIC-006 · approved · source: plan:EPIC-006

LLM extraction pulls buried clues from free-text notes and imaging reports as structured findings with the quoted source sentence. LLM-written clinician summaries and patient visit-prep text are generated from the evidence set with a citation on every sentence.

- Assumptions:
  - Uses a hosted LLM API and needs a credential configured as <llm-api-key>.
  - The dataset's notes are template sentences, so extractor accuracy flatters real-world performance and should be reported as such.
- Story points on stories: 18.

**Related:** US-015, US-016, US-017

### EPIC-007 · approved · source: plan:EPIC-007

The clinician desktop experience: a worklist sorted by status, a one-page case summary with evidence for and against, one-click drill into the timeline, suggested workup, and decision capture. It also covers the Insufficient-history detail screen, the referral packet export and the clinician-invites-patient flow.

- Assumptions:
  - Four previously undesigned screens are in scope: the look-alike case summary, the Insufficient-history detail screen, the referral packet export (printable/PDF) and the post-workup patient update.
  - The six static HTML files in design/ are the visual source of truth.
  - Test ordering, e-prescribing, scheduling and billing integrations are out of scope, so the suggested workup is advisory text only.
- Plan tasks: compose the case payload in GET /api/cases/{patient_id}; build the one-page case summary layout.
- Story points on stories: 42.

**Related:** US-018, US-019, US-020, US-021, US-022, US-023, US-024, US-025, US-026, US-019-T1, US-019-T2

### EPIC-008 · approved · source: plan:EPIC-008

The patient mobile-first experience: a roughly ten-minute symptom intake with one question per screen and a why-we-ask explanation, a plain-language visit-prep sheet, sharing by unguessable link and QR code, and a post-workup update.

- Assumption: patient-facing copy never names a likely diagnosis and never shows a tier or score. This is a structural consequence of the FDA non-device CDS posture, not a styling choice.
- Plan tasks: intake endpoints with resumable progress; one-question-per-screen intake UI.
- Story points on stories: 21.

**Related:** US-027, US-028, US-029, US-030, US-027-T1, US-027-T2

### EPIC-009 · approved · source: plan:EPIC-009

Email-and-password accounts with two roles, clinician and patient. The role boundary enforces the regulatory split: the risk tier and any underlying score exist only on the clinician side.

- Assumptions:
  - No SSO, SMART-on-FHIR or EHR launch. Patients enter via a tokenised invite link that selects a synthetic persona.
  - Access is by invitation only. There are no payments, billing, pricing or subscriptions anywhere, so no commercial epic exists for this scope.
- Story points on stories: 15.

**Related:** US-031, US-032, US-033

### EPIC-010 · approved · source: plan:EPIC-010

Four non-negotiable guardrails implemented as automated checks that can fail the build, not as written policy. They cover post-cutoff data, uncited generated sentences, tier or diagnosis names in patient copy, and the synthetic-data banner.

- Guardrails:
  - No post-cutoff data reaches scoring or display.
  - No uncited sentence appears in any generated summary.
  - No risk tier or named likely diagnosis appears in patient-facing copy.
  - A synthetic-data banner appears on every screen.
- Story points on stories: 13.

**Related:** US-034, US-035, US-036, US-037

### EPIC-011 · approved · source: plan:EPIC-011

The scripted demo path that ships first. It has a picker over the six hero personas from heroes.json and an odyssey replay of what happened versus what would have happened, with the lead time. The performance budget is under sixty seconds from persona selection to a rendered case summary.

- The six personas are the product's acceptance tests.
- Assumption: the six static HTML files in design/ are the visual source of truth for these screens.
- Story points on stories: 16.

**Related:** US-038, US-039, US-040, US-041

### EPIC-012 · approved · source: plan:EPIC-012

An internal, clinician-side evaluation view that runs the engine across a split and computes the PRD success metrics in-product. Demo numbers come from the system, not a side script.

- Assumption: this view is the only component permitted to read ground truth from the quarantined labels store. The test split is reported once per training run.
- Plan tasks: evaluation job in the worker; evaluation endpoints with role enforcement; evaluation report screen.
- Story points on stories: 8.

**Related:** US-042, US-042-T1, US-042-T2, US-042-T3

### EPIC-013 · approved · source: plan:EPIC-013

Both sides ship as a single responsive web application, with patient screens mobile-first and clinician screens for desktop. It is deployed as a managed web app in a US region, with configuration supplied as environment settings.

- Assumptions:
  - No native iOS or Android app is built.
  - PostgreSQL backs the unified event store.
  - SOC 2 and HITRUST certification and any formal FDA submission are out of scope for this release, though the design must not block them.
- Configuration is supplied as environment settings, e.g. <database-connection-string> and <llm-api-key>.
- Story points on stories: 8.

**Related:** US-043, US-044

### SPRINT-1 · draft · source: plan:SPRINT-1

Sprint 1 goal: foundation. A deployable app skeleton, dataset ingest into the unified event store, and the synthetic-data banner. Capacity is 20.

- Goal: Foundation: deployable app skeleton, dataset ingest into the unified event store, synthetic-data banner.
- Capacity: 20.
- Plan status: generated, version 1.
- The input does not list the items assigned to this sprint.

### SPRINT-2 · draft · source: plan:SPRINT-2

Sprint 2 goal: provenance on every row, the condition pack, clinician sign-in and patient invite generation. Capacity is 20.

- Goal: Provenance on every row, condition pack, clinician sign-in and patient invite generation.
- Capacity: 20.
- Plan status: generated, version 1.
- The input does not list the items assigned to this sprint.

### SPRINT-3 · draft · source: plan:SPRINT-3

Sprint 3 goal: label quarantine, cutoff-safe inputs, encounter de-duplication and LLM credential configuration. Capacity is 20.

- Goal: Label quarantine, cutoff-safe inputs, encounter de-duplication, LLM credential configuration.
- Capacity: 20.
- Plan status: generated, version 1.
- The input does not list the items assigned to this sprint.

### SPRINT-4 · draft · source: plan:SPRINT-4

Sprint 4 goal: note clue extraction, ASAS/SPARTAN criteria and the post-cutoff guardrail. Capacity is 20.

- Goal: Note clue extraction, ASAS/SPARTAN criteria, post-cutoff guardrail.
- Capacity: 20.
- Plan status: generated, version 1.
- The input does not list the items assigned to this sprint.

### SPRINT-5 · draft · source: plan:SPRINT-5

Sprint 5 goal: counter-evidence caps, tier output with Insufficient history, and the clinician worklist. Capacity is 20.

- Goal: Counter-evidence caps, tier output with Insufficient history, clinician worklist.
- Capacity: 20.
- Plan status: generated, version 1.
- The input does not list the items assigned to this sprint.

### SPRINT-6 · draft · source: plan:SPRINT-6

Sprint 6 goal: the one-page case summary, evidence-to-source links and patient invite entry. Capacity is 20.

- Goal: One-page case summary, evidence-to-source links, patient invite entry.
- Capacity: 20.
- Plan status: generated, version 1.
- The input does not list the items assigned to this sprint.

### SPRINT-7 · draft · source: plan:SPRINT-7

Sprint 7 goal: offline training, hybrid live scoring, suggested workup and decision capture. Capacity is 20.

- Goal: Offline training, hybrid live scoring, suggested workup, decision capture.
- Capacity: 20.
- Plan status: generated, version 1.
- The input does not list the items assigned to this sprint.

### SPRINT-8 · draft · source: plan:SPRINT-8

Sprint 8 goal: patient intake, the patient timeline and role split enforcement. Capacity is 20.

- Goal: Patient intake, patient timeline, role split enforcement.
- Capacity: 20.
- Plan status: generated, version 1.
- The input does not list the items assigned to this sprint.

### SPRINT-9 · draft · source: plan:SPRINT-9

Sprint 9 goal: cited text generation, the citation verifier and the Insufficient-history detail screen. Capacity is 20.

- Goal: Cited text generation, citation verifier, Insufficient-history detail screen.
- Capacity: 20.
- Plan status: generated, version 1.
- The input does not list the items assigned to this sprint.

### SPRINT-10 · draft · source: plan:SPRINT-10

Sprint 10 goal: visit prep, sharing by link/QR, visible gaps and the patient-copy guardrail. Capacity is 20.

- Goal: Visit prep, share by link/QR, visible gaps, patient-copy guardrail.
- Capacity: 20.
- Plan status: generated, version 1.
- The input does not list the items assigned to this sprint.

### SPRINT-11 · draft · source: plan:SPRINT-11

Sprint 11 goal: the in-app evaluation report, the demo persona picker, the 60-second performance path and responsive polish. Capacity is 20.

- Goal: In-app evaluation report, demo persona picker, 60-second performance path, responsive polish.
- Capacity: 20.
- Plan status: generated, version 1.
- The input does not list the items assigned to this sprint.

### SPRINT-12 · draft · source: plan:SPRINT-12

Sprint 12 goal: odyssey replay, referral packet, workup outcomes and the post-workup patient update. Capacity is 20.

- Goal: Odyssey replay, referral packet, workup outcomes and post-workup patient update.
- Capacity: 20.
- Plan status: generated, version 1.
- The input does not list the items assigned to this sprint.

### SPRINT-13 · draft · source: plan:SPRINT-13

Sprint 13 goal: the persona acceptance suite and editable code lists. Capacity is 20.

- Goal: Persona acceptance suite and editable code lists.
- Capacity: 20.
- Plan status: generated, version 1.
- The input does not list the items assigned to this sprint.
<!-- sdlc:auto:end narrative -->
