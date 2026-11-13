# Planning

> Maintained by QuorQ AI SDLC. Text between `sdlc:auto` markers is regenerated; anything outside them is yours and is kept.

<!-- sdlc:auto:start narrative -->
### EPIC-001 · approved · source: planning:EPIC-001

Admin-run, load-once ingest of the supplied synthetic dataset v0.1 into a normalised unified-event model with provenance on every row. Covers patients, labels, ~572k events, ~40k notes, intake, coverage, encounter truth, hero personas and bulk FHIR NDJSON.

Goal: load the supplied dataset files (patients.csv, labels.csv, events.csv ~572k rows, notes.csv ~40k, intake.csv, coverage.csv, encounter_truth.csv, heroes.json, fhir/*.ndjson.gz) once, by an admin step, into a normalised unified-event store.

Assumptions surfaced in this epic:
- PostgreSQL holds the loaded dataset in a normalised unified-event model with provenance on every row; files are loaded once by an admin ingest step rather than parsed per request, so a persona renders well inside the 60-second demo budget.
- The product ingests these files and never generates a cohort — the synthetic data generator is explicitly out of scope.
- labels.csv is ground truth for evaluation only and is physically separated from anything the engine can read.

**Related:** US-001, US-002, US-003, US-004, REQ-F-008, NFR-021, NFR-023

### EPIC-002 · approved · source: planning:EPIC-002

One chronological timeline per patient merging records, claims and self-reported answers, every item tagged Record / Insurance claim / You told us. Fragmentation in the data is made visible rather than hidden.

Goal: the merged health story, surfacing self-paid care, unconnected providers, pre-coverage periods, payer switches and short reachable history.

Assumption surfaced in this epic: roughly 32% of true encounters appear in no source and 6% of patients have only ~10 months reachable history; the product's job is to state what it cannot see, not to interpolate it.

**Related:** US-005, US-006, REQ-F-002

### EPIC-003 · approved · source: planning:EPIC-003

All condition-specific logic — code lists, signals, ASAS/SPARTAN criteria, counter-evidence rules, suggested workup and patient-facing copy — isolated in a configuration-driven axSpA condition pack, so a second condition would be configuration rather than a rewrite.

Assumptions surfaced in this epic:
- Only the axSpA pack ships in this release; a second pack (lupus, endometriosis) is explicitly out of scope, so the pack boundary is proven by structure and by an automated check, not by a second pack existing.
- The clinical advisor is deferred, so code lists, thresholds, counter-evidence rules and patient wording are flagged as awaiting clinical sign-off but do not block the build.

**Related:** US-007, US-008, REQ-F-008, NFR-019, NFR-027

### EPIC-004 · approved · source: planning:EPIC-004

The explainable half of the engine: score each patient strictly as of their eval_cutoff_date, evaluate ASAS referral criteria and SPARTAN points, apply counter-evidence rules that cap the tier and name the alternative, and output a tier rather than a bare score.

Tier outputs: High / Moderate / Low / Insufficient history.

Assumption surfaced in this epic: a plain ASAS/SPARTAN rules layer flags 95% of osteitis condensans ilii, 85% of sports and 70% of HLA-B27-positive mechanical look-alikes, against a target of under 10% false-High each — so the counter-evidence and demotion rules are load-bearing rather than decoration, and their thresholds are flagged as awaiting clinical sign-off.

**Related:** US-009, US-010, US-011, US-012, REQ-F-004, NFR-013, NFR-015

### EPIC-005 · approved · source: planning:EPIC-005

The precision half of the engine: an in-system offline job that builds features, trains on the train split, tunes the operating threshold on validation, reports test once, and persists a model artefact plus threshold that live scoring applies alongside the rules layer.

Assumptions surfaced in this epic:
- CONFLICT RECORDED, not resolved: the Lightweight MVP baseline described rules-only scoring with an optional dataset-supplied score column; the confirmed understanding supersedes this because the dataset contains no score column and the model is trained inside the system. Both versions are kept on record (see also REQ-003 and REQ-F-004).
- Training runs as a backend job, is not retrained per request, and clinician feedback does not retrain it in this build.

**Related:** US-013, US-014, REQ-F-004, NFR-020, NFR-022, NFR-029

### EPIC-006 · approved · source: planning:EPIC-006

LLM extraction pulls buried clues out of free-text notes and imaging reports, returning a structured finding plus the quoted source sentence. LLM-written clinician summaries and patient visit-prep text are generated from the evidence set with a citation on every sentence.

Assumptions surfaced in this epic:
- This uses a hosted LLM API and requires a credential configured as <llm-api-key>.
- The dataset's notes are template sentences, so extractor accuracy here will flatter real-world performance and should be reported as such.

**Related:** US-015, US-016, US-017, REQ-F-004, REQ-002, NFR-011, NFR-028

### EPIC-007 · approved · source: planning:EPIC-007

The clinician desktop experience: a worklist sorted by status, a one-page case summary readable in under two minutes, one-click drill into the timeline, suggested workup with reasoning, decision capture, the Insufficient-history detail screen, the referral packet export and the clinician-invites-patient flow.

Assumptions surfaced in this epic:
- The four previously undesigned screens — the look-alike case summary, the Insufficient-history detail screen, the referral packet export as a printable/PDF summary, and the post-workup patient update — are in scope.
- The six static HTML files in design/ are the visual source of truth.
- Test ordering, e-prescribing, scheduling and billing integrations are out of scope, so the suggested workup is advisory text only.

**Related:** US-018, US-019, US-020, US-021, US-022, US-023, US-024, US-025, US-026, REQ-F-003, NFR-002, NFR-015

### EPIC-008 · approved · source: planning:EPIC-008

The patient mobile-first experience: a roughly ten-minute symptom intake one question per screen with a 'why we ask' explanation, a plain-language visit-prep sheet, sharing by unguessable link rendered as a QR code, and a post-workup update.

Assumption surfaced in this epic: patient-facing copy never names a likely diagnosis and never shows a tier or score — a structural consequence of the FDA non-device clinical decision support posture, not a styling choice.

**Related:** US-027, US-028, US-029, US-030, REQ-F-002, NFR-003, NFR-016

### EPIC-009 · approved · source: planning:EPIC-009

Email-and-password accounts with two roles, clinician and patient, where the role boundary enforces the regulatory split: the risk tier and any underlying score exist only on the clinician side.

Assumptions surfaced in this epic:
- No SSO, no SMART-on-FHIR and no EHR launch; patients enter via a tokenised invite link that selects a synthetic persona.
- Access is by invitation only and there are no payments, billing, pricing or subscriptions anywhere in the product, so no commercial epic exists for this scope.

**Related:** US-031, US-032, US-033, REQ-F-001, NFR-010, NFR-012, NFR-030

### EPIC-010 · approved · source: planning:EPIC-010

The four non-negotiable guardrails implemented as automated, testable rules rather than written policy. Each runs as a check that can fail the build.

The four guardrails:
- No post-cutoff data reaching scoring or display.
- No uncited sentence appearing in any generated summary.
- No risk tier or named likely diagnosis in patient-facing copy.
- A synthetic-data banner on every screen.

**Related:** US-034, US-035, US-036, US-037, REQ-F-005, NFR-013, NFR-014, NFR-017

### EPIC-011 · approved · source: planning:EPIC-011

The scripted demo path that ships first: a picker over the six hero personas from heroes.json, an odyssey replay showing what happened versus what would have happened with the lead time, and a sixty-second budget from persona selection to a rendered case summary.

The six personas are the product's acceptance tests.

Assumption surfaced in this epic: the six static HTML files in design/ are the visual source of truth for these screens.

**Related:** US-038, US-039, US-040, US-041, REQ-F-006, NFR-001

### EPIC-012 · approved · source: planning:EPIC-012

An internal, clinician-side evaluation view that runs the engine across a split and computes the PRD's success metrics in-product, so demo numbers come from the system rather than from a side script.

Assumption surfaced in this epic: this view is the only component permitted to read ground truth from the quarantined labels store, and the test split is reported once per training run.

**Related:** US-042, REQ-F-007, NFR-012, NFR-028

### EPIC-013 · approved · source: planning:EPIC-013

Both sides ship as a single responsive web application — patient screens mobile-first for phone browsers, clinician screens for desktop — deployed as a managed web app in a US region with configuration supplied as environment settings.

Assumptions surfaced in this epic:
- No native iOS or Android app is built.
- PostgreSQL backs the unified event store.
- SOC 2 and HITRUST certification and any formal FDA submission are out of scope for this release, though the design must not block them.

**Related:** US-043, US-044, REQ-001, NFR-004, NFR-011
<!-- sdlc:auto:end narrative -->
