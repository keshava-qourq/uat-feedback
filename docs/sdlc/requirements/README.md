# Product Requirements

> Maintained by QuorQ AI SDLC. Text between `sdlc:auto` markers is regenerated; anything outside them is yours and is kept.

<!-- sdlc:auto:start narrative -->
## Summary

### REQ-001 · approved · source: requirements:technology_stack

The product owner approved a fixed four-part technology stack: FastAPI 0.115 backend, AWS cloud, PostgreSQL 16 database and React 19 frontend. The requirement states these must be designed against exactly, with no substitutions. Each choice is tied to work already done or to the demo's constraints.

Approved stack — design against exactly these; do not substitute:

- Backend: FastAPI 0.115. The scoring engine, the leakage-safe cutoff logic and the evaluation metrics are already written and reasoned about in Python (baseline.py and the dataset tooling). FastAPI keeps the condition pack, the ingest of ~800k rows of CSV/NDJSON, the de-duplication against encounter_truth.csv and the metrics view in the same language, so clinical logic moves across rather than being re-implemented and re-validated in another language.
- Cloud: AWS. A standard managed web app in a US region: managed Postgres, the app itself, and object storage for the dataset files uploaded once. Named as the environment clinical advisors and investors expect, and the clearest path to the HIPAA-eligible configuration and SOC 2 work deliberately deferred — so today's PoC does not have to be rebuilt when real patient data eventually arrives.
- Database: PostgreSQL 16. The unified event model (one row per fact per source, provenance on every row) is a relational table, and the central product promise — every flag links back to the record that produced it — is a join. Postgres holds 572k events, 167k truth rows and 40k notes, indexes them by patient and event_time so a persona renders inside the 60-second demo budget, and its full-text search covers finding wording inside notes without a separate search engine.
- Frontend: React 19. One codebase serves two different screens: a one-question-per-screen intake and timeline that work on a phone, and a dense clinician worklist and case summary read in under two minutes on a desktop. React handles both in a single responsive app; the odyssey replay animation, evidence chips that drill into the timeline in one click, and QR share are well-trodden there. It also matches the assumption already recorded for this build.

**Related:** REQ-002, REQ-003, NFR-005, NFR-023

### REQ-002 · approved · source: requirements:services

Five runtime services were approved and must all be included in runtime_needs: Anthropic (Claude) as the AI provider, Redis as both queue and cache, Amazon S3 for file storage and SendGrid for email. Each carries a stated purpose tied to a product capability. The required configuration keys are listed and supplied as deployment configuration only.

Approved services (include exactly these in runtime_needs):

- AI provider — Anthropic (Claude), SaaS, env ANTHROPIC_API_KEY. Reads the 40k free-text notes and imaging reports and pulls out the deciding details (iliac-side-only sclerosis, no erosions, postpartum timing), returning the exact quoted sentence so every clue keeps its source link.
- Queue — Redis as a queue, container redis:7-alpine. Loading the dataset, de-duplicating encounters and running the LLM extractor over 40k notes takes minutes, not seconds; these run as background jobs with progress shown, so admin ingest and the full-cohort metrics run never block a screen.
- Cache — Redis, container redis:7-alpine. Keeps the computed worklist, persona summaries and evaluation numbers warm so the scripted demo opens a case well inside the 60-second budget instead of recomputing on every click.
- File storage — Amazon S3, SaaS, env AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, S3_BUCKET. Holds the uploaded dataset files (including the compressed FHIR NDJSON) and the generated referral-packet PDFs, so large files sit in storage rather than in the database or on the app server's disk.
- Email — SendGrid, SaaS, env SENDGRID_API_KEY. Sends the tokenised invite links that let patients and clinical advisors into the invitation-only PoC, plus password resets — the only outbound mail the product needs.

Configuration keys the app needs (names only; values are deployment configuration and must never appear in source control, logs or on any screen — see NFR-011): ANTHROPIC_API_KEY, AWS_ACCESS_KEY_ID, AWS_REGION, AWS_SECRET_ACCESS_KEY, REDIS_URL, S3_BUCKET, SENDGRID_API_KEY. Values are supplied as placeholders such as <llm-api-key> and <database-connection-string>.

**Related:** REQ-001, NFR-006, NFR-011, NFR-022

### REQ-003 · approved · source: requirements:scope

Scope is an invitation-only internal proof of concept for an axSpA condition pack running wholly on supplied synthetic data. In scope: dataset ingest, unified timeline with provenance and gaps, leakage-safe rules-based tiering, clinician case summary and worklist, demo personas and an evaluation report. Explicitly out of scope: a synthetic data generator, a native mobile app, live EHR/payer integrations, ordering/prescribing/scheduling/billing, certifications and a second condition pack.

In scope (capabilities):
- Admin ingest of the supplied CSV, JSON and FHIR NDJSON dataset files.
- Unified timeline tagged Record / Insurance claim / You told us.
- Visible gaps where care was self-paid, unconnected or pre-coverage.
- Pluggable axSpA condition pack: codes, signals, criteria, workup, copy, ASAS referral criteria and SPARTAN points evaluation.
- Counter-evidence rules that cap the tier and name the alternative.
- Leakage-safe scoring as of each patient's evaluation cutoff date.
- Tier output: High / Moderate / Low / Insufficient history, never a score.
- One-page clinician case summary readable in under two minutes.
- Top evidence items linked to the source record behind each.
- Evidence against, and conflicting labels already in the record.
- Criteria met and criteria missing, shown side by side.
- One-click drill from the case summary into the full timeline.
- Suggested workup with the reasoning for each item.
- Worklist sorted by status with reason and reachable history.
- Insufficient-history screen with a "what we still need" list.
- Demo persona picker over the six hero personas.
- Clinician sign-in.
- Rules-only scoring in the product; no model trained in the app.
- Optional per-patient model score column shown when the dataset supplies one.
- Code lists (ICD-10, CPT, LOINC, HLA-B27, ATC) as editable pack configuration.
- EHR/claim encounter de-duplication checked against encounter_truth.csv.
- Insufficient history set by a reachable-history threshold.
- One responsive web app: patient mobile-first, clinician desktop.
- No payments or billing; invitation-only internal proof of concept.

Out of scope — do not design or build:
- Synthetic patient data generator.
- Native mobile app for the patient side.
- Live EHR, health-portal and insurer connections (SMART-on-FHIR, payer APIs).
- Test ordering, e-prescribing, scheduling and billing integrations.
- SOC 2 / HITRUST certification and formal FDA submission.
- A second condition pack (lupus, endometriosis) in this release.

Note: the input records "Rules-only scoring in the product; no model trained in the app" in scope while the scoring-engine feature group also describes an offline training job and live scoring from a stored model artefact; both statements are recorded as given (see REQ-013).

Status: approved. Requirements version 1. Delivery scope: lightweight.

**Related:** REQ-001, REQ-002, NFR-018, NFR-025, NFR-026

### REQ-010 · approved · source: requirements:feature:Sign-in & invites

Access to the proof of concept is by invitation only, with two roles. Clinicians sign in with email and password and land on their worklist, with decisions attributed to their account. Patients enter through a single-use tokenised invite link generated by a clinician, scoped to exactly one synthetic patient's data.

Requirements in this group:

- Clinician sign-in and sign-out: clinicians sign in with their email address and a password and land on their worklist; every decision they record is attributed to their account. Signing out ends the session straight away. An administrator can deactivate an account so it can no longer be used.
- Patient entry by invite link: an invited patient opens the link they were sent and is given access to exactly one synthetic patient's own data, with the option to set a password so they can return. An expired, revoked or already-used link is refused with a plain message and shows no patient data.
- Clinician invites a patient: from the worklist or an open case, a clinician generates a single-use invite link for a patient and is shown it to send on. The patient's row then shows whether the invite is not yet opened, opened, or the intake is completed.

Related qualities: sessions end on sign-out, idle expiry and deactivation (NFR-007); passwords held only as salted hashes with new accounts created without a usable password, set as <set-at-first-login> (NFR-008); unguessable, scoped, expiring and revocable tokens (NFR-009); no unauthenticated or self-service access (NFR-010); email and password only, no SSO (NFR-030, accepted risk).

**Related:** NFR-007, NFR-008, NFR-009, NFR-010, NFR-030

### REQ-011 · approved · source: requirements:feature:Patient app

The patient side is a mobile-first view of the patient's own data only: a merged chronological health story, visible gaps in the record, a one-question-per-screen symptom intake, a plain-language visit-prep sheet, a revocable share link or code, and a non-alarming update when workup results come back. No status, score or suspected diagnosis appears anywhere on the patient side.

Requirements in this group:

- Unified health story timeline: records, insurance claims and the patient's own answers merged into one chronological list; each item carries a date, a plain-language description and a source tag reading Record, Insurance claim or You told us. Tapping an item shows the provider or organisation where known. No risk status or suspected diagnosis appears anywhere on the patient side.
- Visible gaps in the history: coverage gaps and pre-coverage periods are drawn as visible gaps labelled with the reason available from the data. Self-paid care reported at intake appears as a You told us item marked as not confirmed by any record or claim. When reachable history is shorter than the reported symptom duration, a banner states how far back the history goes and invites the patient to add what is missing.
- Symptom intake one question at a time: the condition pack's intake questions are asked one per screen, each with a short "why we ask" explanation, covering stiffness, night pain, response to anti-inflammatories, alternating buttock pain, family history, a body map and self-paid visits. Answers are saved as the patient goes so they can leave and resume at the next unanswered question. Each completed answer becomes a patient-sourced event tagged You told us.
- Plain-language visit-prep sheet: a plain-language summary of the history, the patterns worth raising with the dates and sources behind them, and suggested questions to ask the clinician. Printable or saveable as a document.
- Share the case by link or code: from visit prep the patient can create an unguessable share link, also shown on screen as a scannable code, that lets a signed-in clinician open the full clinician case. The patient can see that a link is active and revoke it, after which it no longer grants access. Each access is recorded against the case.
- Update after tests come back: when a clinician records a negative workup outcome, the patient sees a plain, non-alarming update naming which tests were done, that they came back negative, and what the clinician suggested next. The tests and their results also appear on the patient's timeline tagged Record with their dates.

**Related:** NFR-003, NFR-004, NFR-009, NFR-012, NFR-016, NFR-024

### REQ-012 · approved · source: requirements:feature:Clinician worklist & cases

Clinicians work from a status-ordered worklist into a one-page case summary that shows status, rationale, evidence for and against, conflicting labels, criteria met and missing, and a suggested workup. Every evidence item links back to its source record and drills into the timeline in one click. Clinicians can record a decision, record a workup outcome, see a dedicated insufficient-history screen, and export a referral packet.

Requirements in this group:

- Worklist sorted by status: assigned synthetic patients listed with status, a one-line reason and reachable history as a span of time. Order: High, then Moderate, then Insufficient history, then Low. Filterable by status; selecting a row opens that patient's case summary.
- One-page case summary: status and a one-line rationale in a top card; top evidence, evidence against, conflicting labels already in the record, criteria met and criteria missing side by side, plus the suggested workup — all reachable without leaving the page. For a look-alike case the named alternative explanation is displayed alongside the evidence against.
- Evidence linked to its source: every evidence item carries a date, a source tag of Record, Insurance claim or You told us, and a link resolving to the specific source record or quoted note sentence. Clicking an item opens the full timeline positioned at that item in a single click.
- Suggested workup with reasoning: for patients above Insufficient history, the case lists the pack's workup items, each with a patient-specific reason referencing the evidence or missing criterion that prompted it. Items already performed within reachable history are shown as done with date and result. The list is labelled as information to consider — no order, prescription, appointment or bill is raised from it.
- Record a decision with a reason: a clinician records agree, disagree or need more info with a reason, saved with their identity, the timestamp and the status shown at the time. The decision and who recorded it are visible on the case and in the worklist; a new decision supersedes the earlier one while keeping it in history.
- Insufficient-history detail screen: for a patient with too little data, the case opens a dedicated screen showing the reachable history span, the reason it is limited (e.g. an insurer or employer change) and a "what we still need" list. Each entry names a concrete missing input — the patient's symptom intake, records before a stated date, or a specific test — and states what it would resolve.
- Export a referral packet: from an open case, a printable or PDF packet containing status, evidence for and against, conflicting labels, criteria met and missing, the suggested workup with reasoning and the relevant timeline extract. Every cited item shows its date and source tag.
- Record a workup outcome: results of the suggested workup recorded against the case with the date and the recording clinician. A recorded negative outcome lowers the status according to the condition pack's rules, shows the outcome as the reason for the change, and keeps the prior status visible in the case history.

**Related:** NFR-002, NFR-004, NFR-014, NFR-015, NFR-016, NFR-024

### REQ-013 · approved · source: requirements:feature:Scoring & evidence engine

The engine builds each patient's input set strictly from pre-cutoff events, evaluates referral criteria and points, applies counter-evidence caps and outputs a status of High, Moderate, Low or Insufficient history — never a bare score. An offline job trains a model and tunes a threshold on separate splits, and live scoring applies the stored artefact with the rules layer applied afterwards. A free-text extractor and a cited text generator supply the clinician and patient narratives.

Requirements in this group:

- Score only before the cutoff: the input set is built from events dated before that patient's evaluation cutoff date only, with undated family-history rows always allowed. For a confirmed case whose cutoff sits before diagnosis, neither the diagnosis nor its workup appears in the evidence, criteria or timeline shown with the case.
- Evaluate referral criteria and points: each referral criterion and points item is listed as met, not met, or unknown from available data, with the points total shown against the referral threshold held in the condition pack. Opening a met criterion names the underlying event or intake answer with its date and source tag; an unknown item states what would be needed to answer it rather than counting silently as not met.
- Counter-evidence caps the status: pack rules — e.g. iliac-side-only sclerosis without erosions with postpartum timing; widespread pain with normal inflammatory markers and poor anti-inflammatory response; load-related changes in athletes — cap the status and name the plausible alternative explanation. Each rule that fired is shown in plain language with the triggering evidence linked to its source record.
- Status output, never a bare score: outputs High, Moderate, Low or Insufficient history as the headline status, with no bare probability or raw score in its place. A patient whose reachable history falls below the pack-configured threshold is set to Insufficient history; changing that threshold changes the affected set on rescoring without a code change.
- Offline training and threshold tuning: a backend job builds features from leakage-safe pre-cutoff inputs, fits the model on the training split alone, tunes the operating threshold on the validation split and evaluates the test split once per run, logging any repeat rather than overwriting the first result. It stores the model artefact, the chosen threshold with its selection objective, and a run record holding dataset version, seed and feature list.
- Live scoring from the stored model: scoring during a session applies the stored model artefact and threshold to the patient's pre-cutoff features with no training in the request, then applies the rules layer's counter-evidence caps afterwards so a capped status can never be raised back to High. Clinician decisions and recorded outcomes are stored as data and change neither the model nor the threshold.
- Extract clues from free text: an extractor reads notes and imaging reports and returns structured findings for the pack's target clues, each with the exact quoted sentence and the reference back to the note, returning nothing rather than inventing a finding when no target clue is present. An extraction report shows notes processed and findings per clue type.
- Generate cited clinician and patient text: the clinician case summary and the patient visit-prep text are written from the assembled evidence set, with every factual sentence carrying a citation resolving to a specific source record with its date and source tag. The patient text is plain language citing the patient's own records and answers, and contains no status, no score and no named likely diagnosis.

Conflict recorded, not resolved: the scope list states "Rules-only scoring in the product; no model trained in the app" and an "optional per-patient model score column shown when the dataset supplies one", while this feature group specifies an offline training job plus live scoring from a stored model artefact. Both statements are carried as given; NFR-022 covers the rules-only fallback when no artefact is available.

**Related:** REQ-003, NFR-013, NFR-014, NFR-019, NFR-020, NFR-022, NFR-029

### REQ-014 · approved · source: requirements:feature:Safety guardrails

Four enforced guardrails back the product's safety claims: post-cutoff data is blocked everywhere, every generated sentence is verified against a resolvable citation, patient-facing wording is scanned for prohibited terms, and a synthetic-data notice appears on every screen and export page. Each guardrail is covered by an automated suite that fails the build on any violation.

Requirements in this group:

- Block post-cutoff data everywhere: an enforced rule keeps data dated on or after a patient's cutoff out of scoring inputs and out of every timeline, case summary, export and evaluation view, with undated family-history rows the only exception. An automated suite reports the count across the loaded cohort and fails the build if it is not zero.
- Verify every generated sentence: a verifier checks each factual sentence in generated clinician and patient text against a linked source record and blocks or visibly flags any sentence whose citation does not resolve. A citation pointing at a record that does not exist, or that belongs to another patient, is treated the same as a missing one.
- Check patient-facing wording: an automated check scans every patient-facing screen, generated text, notification and export for a status, a numeric risk value or a condition name from the active pack's prohibited-term list. A violation fails the build and names the offending string and its location.
- Synthetic-data notice on every screen: every screen in the patient app, the clinician app, the demo replay and the evaluation report shows a visible notice stating the data is wholly synthetic and not for clinical use; the same notice appears on every page of any printable or exported document. An automated suite visits every route and fails the build if the notice is missing anywhere.

**Related:** NFR-012, NFR-013, NFR-014, NFR-015, NFR-017

### REQ-015 · approved · source: requirements:feature:Demo mode

Demo mode presents six hero personas through a picker, an odyssey replay that contrasts the real journey against when the engine would first have flagged, and an automated acceptance suite asserting the expected outcome for each persona. All patient-side guardrails and the synthetic-data notice apply exactly as outside demo mode.

Requirements in this group:

- Hero persona picker: a presenter opens the picker and sees the six hero personas with their name and a one-line description of the journey each illustrates, then chooses the patient view or the clinician view. That persona's timeline, intake answers and case load as of their cutoff date, with the synthetic-data notice and the patient-side guardrails applying exactly as outside demo mode.
- Odyssey replay with lead time: the replay shows the real journey of visits and providers on one track and the point at which the engine would first have reached High or Moderate on the other, states the lead time against the simulated diagnosis date, and lists the facts nobody connected with their sources. For a persona at Insufficient history it shows the point at which the product would have said so and what was missing, rather than a flag that never occurred.
- Automated persona acceptance suite: the six personas' pass tests run automatically —
  * the strong-signals case reaches High at least two years before the simulated diagnosis date;
  * the weak and atypical case reaches Moderate or higher with its conflicting labels named;
  * the two look-alike cases stay below High with counter-evidence and a named alternative;
  * the side-door case is flagged with the eye history and intake-reported self-paid care cited;
  * the sparse-history case shows Insufficient history with a "what we still need" list and no Low status anywhere.

**Related:** NFR-001, NFR-015, NFR-017

### REQ-016 · approved · source: requirements:feature:Evaluation report

An in-app evaluation report runs over a selected split and computes lead time, per-archetype sensitivity, false-High rates per look-alike group, prevalence-reweighted predictive value and the share of thin-data patients shown as Insufficient history. Each metric is displayed next to its target with a pass or fail marker, alongside the split, dataset version, thresholds in force and run date.

Requirement in this group:

- In-app evaluation report: running the report over a selected split computes
  * median lead time at the operating threshold,
  * sensitivity per archetype,
  * false-High rate reported separately for each look-alike group,
  * predictive value re-weighted to the lower real-world prevalence,
  * the share of thin-data patients shown as Insufficient history.
  Each metric is displayed next to its target with a pass or fail marker. The split, dataset version, thresholds in force and run date are stated on the page.

Related constraints: the report is the only component allowed to read ground truth (see REQ-017); access is refused to anyone without the clinician or administrator role (NFR-012); the report must state the caveat that results flatter real-world performance and are not a clinical-accuracy claim (NFR-028); the full-cohort run executes as a background job with progress shown (NFR-006).

**Related:** NFR-012, NFR-028, REQ-017

### REQ-017 · approved · source: requirements:feature:Admin setup & settings

Administrators run a single repeatable ingest of the supplied dataset files with a per-file pass/fail report, and the loaded store keeps full provenance on every fact. Ground truth is held in a separate evaluation-only store the scoring engine cannot read. Encounter de-duplication is checked against the supplied truth file, all condition logic lives as editable pack configuration, and a settings page reports environment, health and the active dataset version with credentials masked.

Requirements in this group:

- One-run dataset ingest and report: an administrator starts a single ingest run that loads the supplied patient, label, event, note, intake, coverage, encounter-truth, persona and bulk FHIR files, reporting per-file rows loaded and rejected. The report shows the dataset version, the seed, the total patient count and a pass or fail line per file, and names any failed file with its reason and column. Re-running ingest replaces the prior load rather than duplicating patients or events.
- Provenance on every stored fact: each stored event keeps its source fields — patient, event time and type, code system and code, value, provider organisation and specialty, source type of record/claim/patient, source reference, encounter reference and confidence — so any item shown anywhere can be traced back. A row missing its source type or source reference is reported as a provenance failure and is not made available to scoring or display.
- Evaluation-only ground-truth store: ground-truth label columns are held in a separate evaluation-only store that the scoring engine cannot read, with only the evaluation cutoff date and split assignment permitted for operational use. The evaluation report is the only component allowed to read ground truth.
- Encounter de-duplication and check: record and claim rows describing the same real encounter are merged into one timeline entry tagged with both contributing sources and counted once in any visit-count signal. A check against the supplied encounter truth file reports how many true encounters matched one merged entry, how many were split, how many rows were merged in error, and how many were invisible in every source and so never shown.
- Condition pack configuration: all condition-specific logic lives in the pack as configuration data — code lists, signal definitions, referral criteria and points, counter-evidence and demotion rules, status thresholds, workup items with their reasoning text, and patient-facing copy strings. With the pack disabled the application still starts and reports that no condition pack is active.
- Editable code lists: an administrator can view and edit the diagnosis, service, laboratory, local marker and drug code lists in the pack, each shown with the signal it maps to. Saving applies the change at the next rescore without a deployment, recording who changed it and when. Equivalent codes created by code drift are recognised as the same signal so counts stay continuous across the change date, and any item awaiting clinical sign-off is marked as such without blocking scoring.
- System settings and deployment status: the administrator page reports the running environment, the health check result and the active dataset version. Credentials such as the hosted language-model key are supplied as deployment configuration and shown only as a masked placeholder (e.g. <llm-api-key>) with a connection status of connected or not configured.

**Related:** NFR-005, NFR-006, NFR-011, NFR-019, NFR-021, NFR-023, NFR-027

### NFR-001 · approved · source: requirements:NFR-001

Performance requirement for the demo path. With the dataset already loaded, picking a hero persona through to a rendered case summary must complete in under sixty seconds end to end. A performance check fails and names the slow stage if any of the six personas exceeds the budget.

Category: performance.

- The whole path from picking a hero persona to a rendered case summary — including timeline assembly, scoring, evidence assembly and summary rendering — must complete in under sixty seconds measured end to end, with the dataset already loaded.
- Already-generated summaries are reused so a repeat open is faster.
- A performance check fails and names the slow stage if any of the six personas exceeds the budget.

Target: under 60 seconds end to end per persona, for all six hero personas.

**Related:** REQ-015, REQ-002

### NFR-002 · approved · source: requirements:NFR-002

Usability requirement for the clinician case summary. The top card alone must let a clinician state the status, the reason and the suggested next step in under two minutes on a desktop browser, with the rest of the case reachable without leaving the page.

Category: usability.

- The one-page case summary must let a clinician state the status, the reason and the suggested next step from the top card alone in under two minutes on a desktop browser.
- The rest of the case must be reachable without leaving the page.

Target: first read in under 2 minutes.

**Related:** REQ-012

### NFR-003 · approved · source: requirements:NFR-003

Usability requirement for the symptom intake. A first-time respondent must be able to complete the one-question-per-screen intake in about ten minutes or less, with progress shown and answers preserved for resume.

Category: usability.

- A first-time respondent must be able to complete the one-question-per-screen symptom intake in about ten minutes or less.
- Progress is shown as a position in the set.
- Answers are preserved so the respondent can leave and resume.

Target: about 10 minutes or less for a first-time respondent.

**Related:** REQ-011

### NFR-004 · approved · source: requirements:NFR-004

Responsiveness requirement for the single web app. Patient screens must render on a phone-sized browser window without horizontal scrolling and be usable one-handed; clinician worklist and case summary must present the case on one desktop page without nested scrolling panes. Both must match the agreed designs.

Category: usability.

- The same web application serves both sides.
- Patient screens render on a phone-sized browser window without horizontal scrolling and are usable with one thumb.
- The clinician worklist and case summary present the case on one desktop page without nested scrolling panes.
- Both must match the agreed designs.

**Related:** REQ-001, REQ-011, REQ-012

### NFR-005 · approved · source: requirements:NFR-005

Scalability requirement for the loaded store. It must hold and index the full supplied dataset by patient and event time so persona and case views are served from the database rather than by parsing raw files on each request.

Category: scalability.

- The loaded store must hold and index the supplied dataset: roughly 5,000 patients, about 572,000 event rows, 167,000 encounter-truth rows, 40,000 notes, intake and coverage rows, and the bulk FHIR resources.
- Indexing is by patient and event time.
- Persona and case views must be served from the loaded database, not by parsing the raw files on each request.

Target: ~5,006 patients, ~572k events, ~167k encounter-truth rows, ~40k notes.

**Related:** REQ-001, REQ-017

### NFR-006 · approved · source: requirements:NFR-006

Long-running work must run as background jobs with visible progress so no screen is blocked. This covers dataset ingest, the encounter de-duplication check, the clue extractor over 40,000 notes, model training and the full-cohort evaluation run.

Category: scalability.

- Work that takes minutes rather than seconds must run as background jobs with progress shown, so no screen is blocked while they run.
- Named workloads: the dataset ingest; the encounter de-duplication check; running the clue extractor over the 40,000 notes; model training; the full-cohort evaluation run.
- Supported by the approved Redis queue service (see REQ-002).

**Related:** REQ-002, REQ-013, REQ-016, REQ-017

### NFR-007 · approved · source: requirements:NFR-007

Session lifecycle requirement. Sessions must end immediately on sign-out, expire after a configured idle period, and stop working for any deactivated account, with no new sign-in succeeding for that account.

Category: security.

- A clinician or patient session must end immediately when the user signs out.
- A session must expire after a configured idle period, so the next action asks the user to sign in again.
- A session must stop working for any account an administrator deactivates, after which no new sign-in for that account succeeds.

**Related:** REQ-010

### NFR-008 · approved · source: requirements:NFR-008

Credential storage requirement. Account passwords must be held only as salted hashes and never in recoverable form. New accounts are created without a usable password so the user sets their own at first sign-in.

Category: security.

- Account passwords must be held only as salted hashes and never in recoverable form.
- New accounts are created without a usable password; the user sets their own at first sign-in, recorded as <set-at-first-login>.

**Related:** REQ-010

### NFR-009 · approved · source: requirements:NFR-009

Token requirement for invite and share links. Tokens must be unguessable with a configured expiry, scoped to one patient's own data in the intended role only, refused once expired, revoked or consumed, and revocation must take effect immediately.

Category: security.

- Invite and share links must use unguessable tokens with a configured expiry.
- They grant access only to the one patient's own data and only in the intended role.
- They are refused once expired, revoked or already consumed.
- They stop granting access immediately when the patient revokes a share link.

**Related:** REQ-010, REQ-011

### NFR-010 · approved · source: requirements:NFR-010

Access model requirement. Every patient and clinician route must refuse unauthenticated requests, and the product offers no public sign-up or self-service entry point of any kind — access is only ever granted by invitation.

Category: security.

- Every patient and clinician route must refuse unauthenticated requests.
- The product offers no public sign-up or self-service entry point of any kind.
- Access is only ever granted by invitation.

**Related:** REQ-003, REQ-010

### NFR-011 · approved · source: requirements:NFR-011

Credential handling requirement. The database connection and the hosted language-model credential must be supplied as deployment configuration, with no credential value appearing in source control, logs or any screen. The settings page shows only a masked placeholder with a connected or not-configured status.

Category: security.

- The database connection and the hosted language-model credential must be supplied as deployment configuration, e.g. <database-connection-string> and <llm-api-key>.
- No credential value may appear in source control, logs or any screen.
- The settings page shows only a masked placeholder with a connected or not-configured status.

**Related:** REQ-002, REQ-017

### NFR-012 · approved · source: requirements:NFR-012

Privacy requirement separating patient and clinician data. No status, score, criteria evaluation or suspected-condition name may reach a patient-role account in any screen or in the data behind it, and refusal must happen at the server rather than being hidden in the browser. An automated check over every patient-facing response must find zero occurrences or fail the build.

Category: privacy.

- No status, score, criteria evaluation or suspected-condition name may be returned to a patient-role account in any screen or in the data behind it.
- Requests from a patient account for clinician screens or clinician data must be refused at the server, not hidden in the browser.
- The evaluation report is refused to anyone without the clinician or administrator role.
- An automated check over every patient-facing response must find zero occurrences or fail the build.

Target: zero occurrences in patient-facing responses.

**Related:** REQ-011, REQ-014, REQ-016

### NFR-013 · approved · source: requirements:NFR-013

Compliance requirement for leakage safety. Scoring inputs, training features and anything rendered for a patient must contain no event dated on or after that patient's evaluation cutoff, with undated family-history rows the only exception, and no ground-truth label column may be used as an input or feature. Automated checks must report zero violations across the loaded cohort or fail the build.

Category: compliance.

- Scoring inputs, training features and anything rendered for a patient must contain no event dated on or after that patient's evaluation cutoff.
- Undated family-history rows are the only exception.
- No ground-truth label column may be used as an engine input or feature.
- Automated checks must report zero violations across the loaded cohort and fail the build otherwise.

Target: zero post-cutoff items and zero ground-truth columns in scoring inputs, features and rendered output.

**Related:** REQ-013, REQ-014, REQ-017

### NFR-014 · approved · source: requirements:NFR-014

Traceability requirement. Every evidence item on a case and every factual sentence in generated text must resolve to an existing source record belonging to that patient. A cohort-wide automated traceability check must report full resolution and zero published uncited sentences, failing otherwise.

Category: compliance.

- Every evidence item on a case and every factual sentence in generated text must resolve to an existing source record belonging to that patient.
- An automated traceability check over the whole cohort must report full resolution and zero published uncited sentences.
- The check fails if any item or sentence cannot be resolved.

Target: 100% of evidence items resolving; zero published uncited sentences.

**Related:** REQ-012, REQ-013, REQ-014, REQ-017

### NFR-015 · approved · source: requirements:NFR-015

Safety requirement that thin data never reads as reassurance. A patient below the reachable-history threshold must show as Insufficient history on every clinician screen, worklist row and export, visually distinct from Low, and must never be labelled Low or given reassuring wording or a numeric risk value. An automated guardrail test fails the build on any occurrence.

Category: compliance.

- A patient below the reachable-history threshold must be shown as Insufficient history on every clinician screen, worklist row and export.
- The Insufficient history state must be visually distinct from Low.
- The word Low, reassuring wording or a numeric risk value must never appear as that patient's status.
- An automated guardrail test checks this and fails the build on any occurrence.

Target: 100% of thin-data patients shown as Insufficient history, zero Low occurrences.

**Related:** REQ-012, REQ-013, REQ-015

### NFR-016 · approved · source: requirements:NFR-016

Regulatory posture requirement: the product is non-device decision support. It must never issue a diagnosis or treatment decision; suggested workup is advisory text only with no order, prescription, appointment or bill raised from it, and the patient side only organises the patient's own data and prompts questions.

Category: compliance.

- The product must never issue a diagnosis or a treatment decision.
- The suggested workup is advisory text only, with no order, prescription, appointment or bill raised from it.
- The patient side only organises the patient's own data and prompts questions; it never names a likely disease and never shows a status or score.

Note: this is a design posture for a human to confirm, not legal advice.

**Related:** REQ-011, REQ-012, REQ-003

### NFR-017 · approved · source: requirements:NFR-017

A visible synthetic-data notice must appear on every route in the patient app, clinician app, demo replay and evaluation report, and on every page of every printable or exported document. The guardrail suite reports notice presence across all routes and a missing banner fails the build.

Category: compliance.

- A visible notice stating that the data is wholly synthetic and not for clinical use must appear on every route in the patient app, the clinician app, the demo replay and the evaluation report.
- The same notice must appear on every page of every printable or exported document.
- The guardrail suite reports the notice present on all routes; a missing banner fails the build.

Target: present on 100% of routes and on every page of every export.

**Related:** REQ-014, REQ-015, REQ-016

### NFR-018 · approved · source: requirements:NFR-018

No commercial flow anywhere in the product. There must be no payment, pricing, billing or subscription step, since this is an invitation-only internal proof of concept.

Category: compliance.

- There must be no payment, pricing, billing or subscription step anywhere in the product.
- Rationale as stated: this is an invitation-only internal proof of concept.

**Related:** REQ-003

### NFR-019 · approved · source: requirements:NFR-019

Maintainability requirement confining condition logic to the pack. No condition-specific identifier may be hard-coded outside the pack, proven by an automated code scan, and changes to code lists, thresholds or wording take effect on rescoring without a deployment. With the pack disabled the application must still start cleanly and report that no pack is active.

Category: maintainability.

- No condition-specific identifier — a condition code, a marker name or a named rule — may be hard-coded outside the condition pack.
- This is proven by an automated scan of the application code.
- Changes to code lists, thresholds or wording take effect on rescoring without a code deployment.
- With the pack disabled the application still starts cleanly and reports that no pack is active.

**Related:** REQ-013, REQ-017

### NFR-020 · approved · source: requirements:NFR-020

Reproducibility requirement for training runs. Each run must persist its model artefact, the chosen operating threshold with its selection objective, and a run record holding dataset version, seed and feature list. The test split is evaluated and recorded once per run, with any repeat logged rather than silently overwriting the first result.

Category: maintainability.

- Each training run must persist: the model artefact; the chosen operating threshold with its selection objective; a run record holding the dataset version, seed and feature list.
- The test split is evaluated and recorded once per run.
- Any repeat is logged rather than silently overwriting the first result.

**Related:** REQ-013

### NFR-021 · approved · source: requirements:NFR-021

Ingest must be repeatable and atomic in effect. Re-running on the same dataset replaces the prior load rather than duplicating patients or event rows, with the final patient count matching the file. A malformed file or missing required column must leave no partially loaded rows queryable and must be named with its reason.

Category: maintainability.

- Re-running ingest on the same dataset must replace the prior load rather than create duplicate patients or event rows, with the final patient count matching the file.
- A malformed file or a missing required column must leave no partially loaded rows queryable by the application.
- Such a file must be named with its reason instead of being silently skipped.

**Related:** REQ-017

### NFR-022 · approved · source: requirements:NFR-022

Availability requirement for degraded dependencies. With no model artefact available the system falls back to rules-only tiering and labels the case as scored without the model; if the language-model credential is missing or the call fails, the case still renders status, evidence and criteria from the structured engine with the narrative section stating that generated text is unavailable.

Category: availability.

- If no model artefact is available, the system must fall back to rules-only tiering and label the case as scored without the model.
- If the language-model credential is missing or the call fails, the case must still render its status, evidence items and criteria from the structured engine, with the narrative section stating that generated text is unavailable.
- Neither situation may fail the page or show an empty status.

**Related:** REQ-013, REQ-002

### NFR-023 · approved · source: requirements:NFR-023

Compatibility requirement for ingest. The dataset must be read exactly as supplied — comma-separated files, JSON and gzipped bulk FHIR newline-delimited JSON for every resource type present — without any manual conversion first.

Category: compatibility.

- Ingest must read the dataset exactly as supplied: comma-separated files, JSON, and gzipped bulk FHIR newline-delimited JSON for every resource type present.
- No file may need to be converted by hand before ingest.

**Related:** REQ-017, REQ-001

### NFR-024 · approved · source: requirements:NFR-024

Exports must be self-contained. The referral packet and the visit-prep sheet must be readable by a rheumatologist or patient without access to the application or an account.

Category: compatibility.

- The referral packet and the visit-prep sheet must be self-contained printable documents.
- They must be readable without access to the application or an account.
- Note: every page of these exports also carries the synthetic-data notice (NFR-017).

**Related:** REQ-011, REQ-012

### NFR-025 · approved · source: requirements:NFR-025

Accepted risk: formal security certification and any regulatory submission are deliberately out of this release. The team accepts shipping the invitation-only internal proof of concept without them, on the condition that the design does not block that work later.

Category: compliance. Marked in the input as an accepted risk.

- Formal security certification and any regulatory submission are deliberately out of this release.
- The product is an invitation-only internal proof of concept and the team accepts that it ships without them.
- Condition of acceptance: the design must not block that work later (see the AWS rationale in REQ-001 regarding the HIPAA-eligible configuration and SOC 2 path).

**Related:** REQ-003, REQ-001

### NFR-026 · approved · source: requirements:NFR-026

Accepted risk: the proof of concept runs entirely on synthetic data, with no real patient information, no live record or insurer connections and no ethics review. The handling controls that real patient data would require are knowingly not built in this release.

Category: privacy. Marked in the input as an accepted risk.

- The proof of concept runs entirely on synthetic data, with no real patient information.
- There are no live record or insurer connections and no ethics review.
- The handling controls that real patient data would require are knowingly not built in this release.

**Related:** REQ-003, NFR-017

### NFR-027 · approved · source: requirements:NFR-027

Accepted risk: code lists, rule thresholds, counter-evidence rules and patient-facing wording ship without clinical review. They are marked in the pack as awaiting clinical sign-off, and that marker is informational only — it does not block scoring or the demo.

Category: compliance. Marked in the input as an accepted risk.

- Code lists, rule thresholds, counter-evidence rules and patient-facing wording ship without clinical review.
- They are marked in the condition pack as awaiting clinical sign-off.
- The marker is informational only and does not block scoring or the demo.

**Related:** REQ-017, REQ-013

### NFR-028 · approved · source: requirements:NFR-028

Accepted risk: because the dataset's notes are template sentences and the cohort is simpler and more enriched than real practice, extraction and metric results will look better here than on real clinical data. The extraction report and the evaluation report must state this caveat and that the numbers prove the pipeline works rather than making a clinical-accuracy claim.

Category: compliance. Marked in the input as an accepted risk.

- The dataset's notes are template sentences and the cohort is simpler and more enriched than real practice.
- Extraction and metric results will therefore look better here than on real clinical data.
- Both the extraction report and the evaluation report must state this caveat, and must state that the numbers prove the pipeline works rather than making a clinical-accuracy claim.

**Related:** REQ-016, REQ-013

### NFR-029 · approved · source: requirements:NFR-029

Accepted risk: clinician decisions and recorded workup outcomes are stored and displayed as data only. In this build they trigger no retraining and no threshold change, and are not used as training data.

Category: maintainability. Marked in the input as an accepted risk.

- Clinician decisions and recorded workup outcomes are stored and displayed as data only.
- The team accepts that in this build they trigger no retraining and no threshold change.
- They are not used as training data.

**Related:** REQ-012, REQ-013

### NFR-030 · approved · source: requirements:NFR-030

Accepted risk: sign-in is deliberately limited to email and password with two roles. Single sign-on, health-record launch and any federated identity are knowingly left out of this proof of concept.

Category: security. Marked in the input as an accepted risk.

- Sign-in is deliberately limited to email and password, with two roles.
- Single sign-on, health-record launch and any federated identity are knowingly left out of this proof of concept.

**Related:** REQ-010
<!-- sdlc:auto:end narrative -->

<!-- sdlc:auto:start summary -->
**Requirements version:** v2  
**Delivery scope:** lightweight  
**Approved:** 2026-11-24

**Capabilities in scope:** Admin ingest of the supplied CSV, JSON and FHIR NDJSON dataset files, Unified timeline tagged Record / Insurance claim / You told us, Visible gaps where care was self-paid, unconnected or pre-coverage, Pluggable axSpA condition pack: codes, signals, criteria, workup, copy, ASAS referral criteria and SPARTAN points evaluation, Counter-evidence rules that cap the tier and name the alternative, Leakage-safe scoring as of each patient's evaluation cutoff date, Tier output: High / Moderate / Low / Insufficient history, never a score, One-page clinician case summary readable in under two minutes, Top evidence items linked to the source record behind each, Evidence against, and conflicting labels already in the record, Criteria met and criteria missing, shown side by side, One-click drill from the case summary into the full timeline, Suggested workup with the reasoning for each item, Worklist sorted by status with reason and reachable history, Insufficient-history screen with a "what we still need" list, Demo persona picker over the six hero personas, Clinician sign-in, Rules-only scoring in the product; no model trained in the app, Optional per-patient model score column shown when the dataset supplies one, Code lists (ICD-10, CPT, LOINC, HLA-B27, ATC) as editable pack configuration, EHR/claim encounter de-duplication checked against encounter_truth.csv, Insufficient history set by a reachable-history threshold, One responsive web app: patient mobile-first, clinician desktop, No payments or billing; invitation-only internal proof of concept

**Approved technology stack:**

| Layer | Choice | Rationale |
|---|---|---|
| backend | FastAPI | The scoring engine, the leakage-safe cutoff logic and the evaluation metrics are already written and reasoned about in Python — your baseline.py and the dataset tooling live there. FastAPI keeps the condition pack, the ingest of ~800k rows of CSV/NDJSON, the de-duplication against encounter_truth.csv and the metrics view in the same language as the work you've already done, so clinical logic moves across rather than being re-implemented and re-validated in another language. |
| cloud | AWS | You asked for a standard managed web app in a US region, which is what this is: a managed Postgres, the app itself, and object storage for the dataset files you upload once. It is also the environment clinical advisors and investors will expect to hear named, and the one with the clearest path to the HIPAA-eligible configuration and SOC 2 work you have deliberately deferred — so today's PoC does not have to be rebuilt when real patient data eventually arrives. |
| database | PostgreSQL | Your unified event model — one row per fact per source, with provenance on every row — is exactly a relational table, and the product's central promise (every flag links back to the record that produced it) is a join. Postgres comfortably holds 572k events, 167k truth rows and 40k notes, indexes them by patient and event_time so a persona renders well inside the 60-second demo budget, and its full-text search covers finding wording inside notes without a separate search engine. |
| frontend | React | One codebase has to serve two very different screens: a one-question-per-screen intake and timeline that work on a phone, and a dense clinician worklist and case summary read in under two minutes on a desktop. React handles both in a single responsive app, and the pieces the demo depends on — the odyssey replay animation, evidence chips that drill into the timeline in one click, QR share — are all well-trodden ground there. It also matches the assumption already recorded for this build. |
<!-- sdlc:auto:end summary -->

<!-- sdlc:auto:start epics -->
## EPIC-001: Dataset ingest and the unified event store

Admin-run, load-once ingest of the supplied synthetic dataset v0.1 (patients.csv, labels.csv, events.csv ~572k rows, notes.csv ~40k, intake.csv, coverage.csv, encounter_truth.csv, heroes.json, fhir/*.ndjson.gz) into a normalised unified-event model with provenance on every row.

Assumptions surfaced here: (a) PostgreSQL holds the loaded dataset in a normalised unified-event model with provenance on every row; files are loaded once by an admin ingest step rather than parsed per request, so that a persona renders well inside the 60-second demo budget; (b) the product ingests these files and never generates a cohort — the synthetic data generator is explicitly out of scope; (c) labels.csv is ground truth for evaluation only and is physically separated from anything the engine can read.

### US-001: Load the supplied dataset files in one admin ingest run

**Priority:** critical

> As a platform administrator, I want to load the supplied CSV, JSON and FHIR NDJSON dataset files into the application in a single ingest run, so that the product serves personas from a loaded database instead of parsing raw files on every request.

| ID | Given | When | Then |
|---|---|---|---|
| AC-001 | the dataset v0.1 files are present in the configured ingest location | an administrator starts the ingest run | patients.csv, labels.csv, events.csv, notes.csv, intake.csv, coverage.csv, encounter_truth.csv, heroes.json and every fhir/*.ndjson.gz resource type are loaded, and the run reports per-file row counts loaded and rows rejected |
| AC-002 | an ingest run has completed | the administrator opens the ingest report | the report shows the dataset version, the seed, the total patient count and a pass/fail line per file, and a failed file is named with the reason rather than silently skipped |
| AC-003 | a dataset file is malformed or a required column is missing | the ingest run reaches that file | the run stops or marks that file failed, no partially loaded rows from it remain queryable by the application, and the error names the file and column |
| AC-004 | the same dataset has already been ingested | the administrator re-runs ingest | the run replaces the prior load rather than creating duplicate patients or duplicate event rows, and the final patient count matches the file |

### US-002: Keep provenance on every stored fact

**Priority:** critical

> As a platform administrator, I want every stored event row to retain its source fields from events.csv, so that any item shown anywhere in the product can be traced back to the record that produced it.

| ID | Given | When | Then |
|---|---|---|---|
| AC-005 | events.csv has been ingested | any stored event row is inspected | it carries patient_id, event_id, event_time, event_type, code_system, code, display, value, unit, provider_org, provider_specialty, source_type (ehr / claim / patient), source_ref, encounter_ref and confidence |
| AC-006 | a stored event derived from a free-text note or imaging report | its source_ref is followed | the matching note or report text in notes.csv is retrieved, confirming source_ref works as the provenance join key |
| AC-007 | an event row that is missing source_type or source_ref | ingest validation runs | the row is reported as a provenance failure in the ingest report and is not made available to scoring or display |

### US-003: Quarantine ground-truth labels away from the engine

**Priority:** critical

> As a platform administrator, I want labels.csv held in an evaluation-only store that scoring cannot read, so that ground truth can never leak into a risk decision.

| ID | Given | When | Then |
|---|---|---|---|
| AC-008 | labels.csv has been ingested | the scoring engine assembles the inputs for a patient | archetype, typicality, clue_density, hla_b27_true and the axSpA label are not present in the input set, and an automated check fails the build if any of them appears |
| AC-009 | the evaluation report is run | it needs ground truth to compute sensitivity and PPV | it reads labels from the evaluation-only store, and this is the only component permitted to do so |
| AC-010 | eval_cutoff_date and the split assignment are needed operationally | the engine or the demo selects a patient | only eval_cutoff_date and split may be read from the labels store, and that permitted list is enforced in code rather than by convention |

### US-004: De-duplicate EHR and claim views of the same encounter

**Priority:** high

> As a platform administrator, I want EHR and claim rows describing the same real encounter merged into one timeline entry that keeps both sources, so that the timeline shows a patient's actual care history rather than double-counted visits.

| ID | Given | When | Then |
|---|---|---|---|
| AC-011 | an encounter recorded in both an EHR source and a claim source | the unified timeline is built | one timeline entry is produced, tagged with both contributing sources, and the visit is counted once in any visit-count signal |
| AC-012 | an ingested dataset | the de-duplication check is run against encounter_truth.csv | the report states how many true encounters were matched to one merged entry, how many were split into more than one entry, and how many source rows were merged in error |
| AC-013 | a true encounter present in encounter_truth.csv but in no EHR or claim source | the de-duplication check is run | it is counted as invisible care and is never created as a visible timeline entry, since the product may only show what its sources contain |

## EPIC-002: Unified timeline with provenance tags and visible gaps

The merged health story: one chronological timeline per patient, every item tagged Record / Insurance claim / You told us, with the fragmentation in the data made visible rather than hidden — self-paid care, unconnected providers, pre-coverage periods, payer switches and short reachable history.

Assumption surfaced here: roughly 32% of true encounters appear in no source and 6% of patients have only ~10 months reachable; the product's job is to state what it cannot see, not to interpolate it.

### US-005: See my records, claims and answers merged into one timeline

**Priority:** critical

> As a patient, I want my records, insurance claims and my own answers shown as one chronological health story, so that I can see my whole history in one place instead of retelling it from scratch.

| ID | Given | When | Then |
|---|---|---|---|
| AC-014 | a patient with events from EHR, claim and patient sources | the patient opens their health story | all items appear in one chronological list, each with a date, a plain-language description and a source tag reading Record, Insurance claim or You told us |
| AC-015 | an item on the timeline | the patient taps it | the detail shows the provider or organisation where known and the source it came from, and no risk tier, score or suspected diagnosis appears anywhere on the screen |
| AC-016 | a patient viewing on a phone-sized browser window | the health story loads | the timeline is readable and navigable without horizontal scrolling |

### US-006: Show the gaps where care was invisible

**Priority:** high

> As a patient, I want the timeline to tell me plainly where parts of my history are missing, so that I know what to add myself rather than assuming the picture is complete.

| ID | Given | When | Then |
|---|---|---|---|
| AC-017 | a patient with a coverage gap or a pre-coverage period in coverage.csv | the health story is displayed | that period is drawn as a visible gap labelled with the reason available from the data, such as before coverage started or between insurers |
| AC-018 | a patient who reported self-paid care in their intake that appears in no record or claim | the health story is displayed | that care appears on the timeline tagged You told us and is marked as not confirmed by any record or claim |
| AC-019 | a patient whose reachable history is shorter than their reported symptom duration | the health story is displayed | a banner states how far back the reachable history goes and invites the patient to add what is missing, without implying anything about their risk |

## EPIC-003: Pluggable axSpA condition pack

All condition-specific logic — code lists, signals, ASAS/SPARTAN criteria, counter-evidence rules, suggested workup and patient-facing copy — is isolated in a configuration-driven condition pack, so that adding a second condition would be configuration rather than a rewrite.

Assumptions surfaced here: (a) only the axSpA pack ships in this release — a second pack (lupus, endometriosis) is explicitly out of scope, so the pack boundary is proven by structure and by an automated check, not by a second pack existing; (b) the clinical advisor is deferred, so code lists, thresholds, counter-evidence rules and patient wording are flagged as awaiting clinical sign-off but do not block the build.

### US-007: Hold all condition logic in one declarative pack

**Priority:** high

> As a engineering lead, I want codes, signals, criteria, counter-evidence rules, workup items and patient copy declared in the axSpA condition pack, so that a second condition later is a configuration job rather than a rewrite of the product.

| ID | Given | When | Then |
|---|---|---|---|
| AC-020 | the running system | the axSpA condition pack is inspected | it contains the code lists, signal definitions, ASAS and SPARTAN criteria, counter-evidence and demotion rules, tier thresholds, suggested workup items with their reasoning text, and the patient-facing copy strings, all as configuration data |
| AC-021 | the application code outside the condition pack | an automated check scans it for axSpA-specific identifiers such as condition codes, HLA-B27 or SPARTAN rule names | the check passes only if no such identifier is hard-coded outside the pack |
| AC-022 | the axSpA pack is disabled in configuration | the application starts | it starts without error and reports that no condition pack is active, rather than failing in generic timeline or ingest code |

### US-008: Edit the code lists as pack configuration

**Priority:** high

> As a platform administrator, I want the ICD-10, CPT, LOINC, local HLA-B27 and ATC code lists editable as pack configuration, so that a clinical informaticist can correct them later without a code change.

| ID | Given | When | Then |
|---|---|---|---|
| AC-023 | the axSpA pack configuration | an administrator opens the code lists | ICD-10-CM diagnosis codes, CPT service codes, LOINC lab codes for CRP and ESR, the local HLA-B27 code and ATC drug codes are each listed with the signal they map to |
| AC-024 | an administrator adds or removes a code and saves the pack | a patient is rescored | the new code list is applied without a code deployment, and the change is recorded with who changed it and when |
| AC-025 | ICD-10 code drift in the dataset where M54.5 splits into M54.50 and M54.59 after 2021-10-01 | back-pain visits are counted for a patient whose history spans that date | all three codes are recognised as the same signal and the visit count is continuous across the split |
| AC-026 | a code list, rule threshold, counter-evidence rule or patient-facing wording item that has not yet had clinical sign-off | an administrator views the pack | it is marked as awaiting clinical review, and the marker is informational only and does not prevent scoring or the demo |

## EPIC-004: Leakage-safe rules scoring and tier assignment

The explainable half of the engine: score each patient strictly as of their eval_cutoff_date, evaluate ASAS referral criteria and SPARTAN points, apply counter-evidence rules that cap the tier and name the alternative, and output a tier — High / Moderate / Low / Insufficient history — never a bare score.

Assumption surfaced here: a plain ASAS/SPARTAN rules layer flags 95% of OCI, 85% of sports and 70% of HLA-B27-positive mechanical look-alikes against a target of under 10% false-High each, so the counter-evidence and demotion rules are load-bearing rather than decoration, and their thresholds are flagged as awaiting clinical sign-off.

### US-009: Score each patient only on data available before their cutoff

**Priority:** critical

> As a engineering lead, I want scoring to use only events dated before the patient's eval_cutoff_date, so that the lead-time claim is honest and the diagnosis cannot leak into its own prediction.

| ID | Given | When | Then |
|---|---|---|---|
| AC-027 | a patient with events both before and after their eval_cutoff_date | the engine builds that patient's input set | only events with event_time earlier than eval_cutoff_date are included, and undated family-history rows are included |
| AC-028 | a confirmed axSpA case whose cutoff is 30 days before diagnosis | the case summary is produced | neither the diagnosis nor its rheumatology workup appears in the evidence, the criteria or the timeline shown with the case |
| AC-029 | an automated leakage test over the loaded cohort | it inspects every input set the engine produced | it reports zero events dated on or after the relevant eval_cutoff_date, and the test fails the build if the count is not zero |

### US-010: Evaluate ASAS referral criteria and SPARTAN points

**Priority:** critical

> As a clinician, I want to see which ASAS referral criteria and SPARTAN points are met and which are missing, so that I can judge the case against criteria I already trust.

| ID | Given | When | Then |
|---|---|---|---|
| AC-030 | a patient scored as of their cutoff | the criteria panel is produced | each ASAS referral criterion and each SPARTAN point item is listed as met, not met, or unknown from available data, with the SPARTAN total shown against the referral threshold in the pack |
| AC-031 | a criterion marked met | the clinician opens it | the underlying event or intake answer is named with its date and source tag |
| AC-032 | a criterion marked unknown from available data | the clinician opens it | it states what would be needed to answer it, and it is never silently counted as not met in the points total |

### US-011: Cap the tier with counter-evidence and name the alternative

**Priority:** critical

> As a clinician, I want the engine to apply counter-evidence rules that lower the tier and name a plausible alternative explanation, so that the tool can say this looks like it but probably is not, instead of flagging every look-alike High.

| ID | Given | When | Then |
|---|---|---|---|
| AC-033 | a patient with imaging wording describing iliac-side-only sclerosis without erosions and symptom onset within months of a delivery date | the engine scores them | the tier is capped below High, the counter-evidence items are listed individually, and the alternative explanation is named as a pattern consistent with osteitis condensans ilii |
| AC-034 | a patient with widespread pain, normal CRP and poor NSAID response | the engine scores them | the tier is capped no higher than Moderate and the counter-evidence items driving the cap are listed |
| AC-035 | an athlete with load-related sacroiliac bone-marrow edema and pain worse with activity | the engine scores them | the load-related pattern is recorded as counter-evidence and the tier is capped below High |
| AC-036 | a counter-evidence rule has fired | the clinician views the case | the rule is shown in plain language with the evidence that triggered it linked to its source record, and is marked as awaiting clinical sign-off where that applies |

### US-012: Output a tier, never a bare score, with an explicit Insufficient history state

**Priority:** critical

> As a clinician, I want the engine to output High, Moderate, Low or Insufficient history rather than a number, so that I am never given false precision, and thin data is never mistaken for reassurance.

| ID | Given | When | Then |
|---|---|---|---|
| AC-037 | any scored patient | the tier is displayed anywhere in the clinician interface | it reads High, Moderate, Low or Insufficient history, and no bare probability or raw score is presented as the headline status |
| AC-038 | a patient whose reachable history is below the Insufficient-history threshold configured in the condition pack | they are scored | the status is Insufficient history, and it is never rendered as Low, no flag, or any wording that implies reassurance |
| AC-039 | a patient at Insufficient history | the automated guardrail test scans every clinician screen, export and worklist row for that patient | the word Low never appears as that patient's status |
| AC-040 | the reachable-history threshold in the condition pack is changed | the cohort is rescored | the set of patients at Insufficient history changes accordingly without a code change, and the threshold in force is shown on the evaluation report |

## EPIC-005: Model training, threshold tuning and live hybrid scoring

The precision half of the engine: an in-system offline job that builds features, trains on the train split, tunes the operating threshold on val, reports test once, and persists a model artefact plus threshold that live scoring then applies alongside the rules layer.

Assumptions surfaced here: (a) the Lightweight MVP baseline described rules-only scoring with an optional dataset-supplied score column — the confirmed understanding supersedes this, because the dataset contains no score column and the model is trained inside the system; this conflict is recorded rather than silently resolved; (b) training runs as a backend job, is not retrained per request, and clinician feedback does not retrain it in this build.

### US-013: Train the model and tune the operating threshold as an offline job

**Priority:** high

> As a engineering lead, I want an in-system job that trains on the train split, tunes the operating threshold on val and reports test once, so that the engine's precision half is reproducible and the reported numbers are not tuned on the test split.

| ID | Given | When | Then |
|---|---|---|---|
| AC-041 | the ingested dataset with its split assignments | the training job runs | features are built only from leakage-safe pre-cutoff inputs, the model is fitted on the train split alone, and no labels.csv ground-truth column is used as a feature |
| AC-042 | a fitted model | the threshold-tuning step runs | the operating threshold is selected using the val split only, and the chosen threshold with its selection objective is written into the run record |
| AC-043 | a tuned model and threshold | the test split is evaluated | the test evaluation is executed and recorded once per training run, and re-running it is logged as a repeat rather than silently overwriting the first result |
| AC-044 | a completed training run | the job finishes | a persisted model artefact, the operating threshold and a run record containing the dataset version, seed and feature list are stored and retrievable |

### US-014: Score live from the persisted artefact combined with the rules layer

**Priority:** high

> As a clinician, I want live scoring to apply the stored model artefact together with the rules and counter-evidence layer, so that cases load fast and every tier reflects both the model and the explainable rules.

| ID | Given | When | Then |
|---|---|---|---|
| AC-045 | a persisted model artefact and operating threshold | a patient is scored during a session | the stored artefact is applied to that patient's pre-cutoff features and no training occurs during the request |
| AC-046 | a model result and a rules result for the same patient | the tier is assembled | the counter-evidence caps from the rules layer are applied after the model contribution, so a capped tier can never be raised back to High by the model alone |
| AC-047 | no persisted model artefact is available | a patient is scored | the system falls back to rules-only tiering, labels the case as scored without the model, and does not fail or show an empty tier |
| AC-048 | a clinician records agree, disagree or need more info on a case | the decision is saved | it is stored as data and shown on the case, and no retraining or threshold change is triggered in this build |

## EPIC-006: LLM clue extraction and cited summary generation

LLM extraction pulls buried clues out of free-text notes and imaging reports, returning a structured finding plus the quoted source sentence; LLM-written clinician summaries and patient visit-prep text are generated from the evidence set with a citation attached to every sentence.

Assumptions surfaced here: (a) this uses a hosted LLM API and requires a credential configured as <llm-api-key>; (b) the dataset's notes are template sentences, so extractor accuracy here will flatter real-world performance and should be reported as such.

### US-015: Extract buried clues from notes and imaging reports with a quoted source

**Priority:** high

> As a clinician, I want clues buried in free text turned into structured findings that quote the sentence they came from, so that a decisive detail in a radiology report is not lost just because it was never coded.

| ID | Given | When | Then |
|---|---|---|---|
| AC-049 | an imaging report describing sacroiliac findings | the extractor runs over it | it returns structured findings for the pack's target clues — including sacroiliitis wording, iliac-side-only sclerosis, presence or absence of erosions, and postpartum timing — each with the exact quoted sentence and the source_ref of the note |
| AC-050 | a note that contains none of the pack's target clues | the extractor runs over it | it returns no findings rather than inventing one, and the note is recorded as processed |
| AC-051 | an extracted finding | it is used as evidence in a case | the quoted sentence and a link to the full note are available from the evidence item |
| AC-052 | the extractor has been run across the cohort | the administrator opens the extraction report | it shows notes processed, findings per clue type, and a stated caveat that the dataset's templated note text makes extraction easier than real clinical text |

### US-016: Generate clinician and patient text with a citation on every sentence

**Priority:** high

> As a clinician, I want the case summary and the patient visit-prep text written from the evidence set with each sentence tied to a source record, so that I can check any statement in the summary rather than trusting generated prose.

| ID | Given | When | Then |
|---|---|---|---|
| AC-053 | a scored patient with an assembled evidence set | the clinician case summary is generated | every factual sentence carries a citation resolving to a specific source record with its date and source tag |
| AC-054 | the same patient | the patient visit-prep text is generated | it is written in plain language, carries citations to the patient's own records and answers, and contains no risk tier, no score and no named likely diagnosis |
| AC-055 | the LLM API credential is not configured or the call fails | a summary is requested | the case still renders with its tier, evidence items and criteria from the structured engine, and the narrative section states that generated text is unavailable |

### US-017: Configure the LLM credential as deployment configuration

**Priority:** medium

> As a platform administrator, I want the hosted LLM API credential supplied as deployment configuration, so that no secret is stored in the codebase or shown in the interface.

| ID | Given | When | Then |
|---|---|---|---|
| AC-056 | a deployment environment | the administrator configures LLM access | the credential is read from configuration as <llm-api-key> and is never written into source control, logs or any screen |
| AC-057 | a configured credential | the administrator opens the system settings page | the credential is shown only as a masked placeholder and the connection status reads connected or not configured |

## EPIC-007: Clinician worklist, case summary and decision capture

The clinician desktop experience: a worklist sorted by status, a one-page case summary readable in under two minutes with evidence for and against, conflicting labels, criteria met and missing side by side, one-click drill into the timeline, a suggested workup with reasoning, decision capture, the Insufficient-history detail screen, the referral packet export (C-4) and the clinician-invites-patient flow (C-6).

Assumptions surfaced here: (a) the four previously undesigned screens — the look-alike case summary, the Insufficient-history detail screen, the referral packet export as a printable/PDF summary, and the post-workup patient update — are in scope; (b) the six static HTML files in design/ are the visual source of truth; (c) test ordering, e-prescribing, scheduling and billing integrations are out of scope, so the suggested workup is advisory text only.

### US-018: Work a worklist sorted by status with the reason and reachable history

**Priority:** critical

> As a PCP, I want my synthetic patients listed by status with a one-line reason and how much history is reachable, so that I can see at a glance who needs attention and how much the tool actually had to work with.

| ID | Given | When | Then |
|---|---|---|---|
| AC-058 | a signed-in clinician with assigned synthetic patients | the worklist loads | each row shows the patient, the status (High, Moderate, Low or Insufficient history), a one-line reason, and the reachable history expressed as a span of time |
| AC-059 | the worklist | it is first displayed | rows are ordered with High first, then Moderate, then Insufficient history, then Low, and the clinician can filter by status |
| AC-060 | a patient at Insufficient history in the worklist | the row is rendered | its status reads Insufficient history and is visually distinct from Low rather than sharing its styling |
| AC-061 | a worklist row | the clinician selects it | the one-page case summary for that patient opens |

### US-019: Read a one-page case summary in under two minutes

**Priority:** critical

> As a PCP, I want a single page giving the status, the top evidence, the evidence against, conflicting labels and the criteria met and missing, so that I can decide within a fifteen-minute visit whether to test or refer.

| ID | Given | When | Then |
|---|---|---|---|
| AC-062 | a scored patient | the case summary opens | the top card shows the status and a one-line rationale, with the top evidence items, evidence against, conflicting labels in the record, criteria met and criteria missing, and the suggested workup all reachable without leaving the page |
| AC-063 | a case summary | a test reader times a first read on a desktop browser | the status, the reason and the suggested next step can be stated from the top card alone in under two minutes |
| AC-064 | a look-alike case such as the osteitis condensans ilii persona | the case summary opens | evidence for and evidence against are shown side by side, the named alternative explanation is displayed, and the status is not High |
| AC-065 | a patient whose record carries a conflicting label such as fibromyalgia or anxiety | the case summary opens | that label is listed as a conflicting label in the record with its source, together with the reason it may not account for the findings |

### US-020: Link every evidence item to the source record behind it

**Priority:** critical

> As a rheumatologist, I want each evidence item on the case summary linked to the record it came from, so that I can verify any claim rather than taking the tool's word for it.

| ID | Given | When | Then |
|---|---|---|---|
| AC-066 | a case summary with evidence for and evidence against | each item is inspected | each carries a date, a source tag of Record, Insurance claim or You told us, and a link that resolves to the specific source record or note sentence |
| AC-067 | an automated traceability check over every case in the cohort | it runs | it reports 100% of evidence items resolving to an existing source record, and fails if any item cannot be resolved |
| AC-068 | an evidence item on the case summary | the clinician clicks through | the full timeline opens positioned at that item in a single click |

### US-021: See a suggested workup with the reasoning for each item

**Priority:** high

> As a PCP, I want a suggested workup where each item states why it is suggested for this patient, so that I can judge the suggestion instead of following a bare checklist.

| ID | Given | When | Then |
|---|---|---|---|
| AC-069 | a scored patient above the Insufficient-history state | the case summary is displayed | the suggested workup lists the items configured in the condition pack, each with a patient-specific reason referencing the evidence or the missing criterion that prompted it |
| AC-070 | a workup item that has already been performed within the patient's reachable history | the workup is displayed | it is shown as already done with its date and result rather than suggested again |
| AC-071 | the suggested workup | it is displayed | it is labelled as information to consider, no order, prescription, appointment or bill can be raised from it, and the product states that it does not issue a diagnosis |

### US-022: Record a decision with a reason

**Priority:** high

> As a clinical advisor working the synthetic worklist, I want to record agree, disagree or need more info with a reason, so that my judgement on each case is captured for the team to review.

| ID | Given | When | Then |
|---|---|---|---|
| AC-072 | an open case summary | the clinician selects agree, disagree or need more info | a reason can be entered and the decision is saved with the clinician's identity, the timestamp and the tier shown at the time |
| AC-073 | a case with a saved decision | it is reopened or seen in the worklist | the decision, its reason and who recorded it are visible, and the decision can be superseded by a new one with the earlier one retained in history |
| AC-074 | a decision has been recorded | the engine next scores that patient | the tier is unchanged by the decision, since feedback is stored as data and does not retrain the model in this build |

### US-023: Open the Insufficient-history detail screen with a what-we-still-need list

**Priority:** high

> As a PCP, I want a dedicated screen for patients with too little data that tells me exactly what is missing, so that I ask for the right records instead of reading thin data as reassurance.

| ID | Given | When | Then |
|---|---|---|---|
| AC-075 | a patient at Insufficient history | the clinician opens the case | the Insufficient-history detail screen opens showing the reachable history span, the reason it is limited such as an insurer or employer change, and a what we still need list |
| AC-076 | the what we still need list | it is displayed | each entry names a concrete missing input such as the patient symptom intake, records before a stated date, or a specific unperformed test, and states what it would resolve |
| AC-077 | the Insufficient-history screen | an automated guardrail test inspects it | no Low tier, no reassuring wording and no numeric risk score is present anywhere on the screen |

### US-024: Export a referral packet as a printable summary

**Priority:** medium

> As a PCP referring to rheumatology, I want to export the case as a printable or PDF referral packet, so that the rheumatologist's first visit starts from the evidence rather than from zero.

| ID | Given | When | Then |
|---|---|---|---|
| AC-078 | an open case summary | the clinician exports the referral packet | a printable document is produced containing the status, evidence for and against, conflicting labels, criteria met and missing, the suggested workup with reasoning, and the relevant timeline extract |
| AC-079 | an exported packet | it is inspected | every cited item shows its date and source tag, the synthetic-data notice appears on every page, and no data dated on or after the patient's cutoff is present |
| AC-080 | an exported packet | it is opened by a rheumatologist | it is self-contained and readable without access to the application |

### US-025: Record a workup outcome and lower the tier

**Priority:** medium

> As a clinician, I want to record the outcome of the suggested workup, so that a case that has been ruled out stops presenting as a live flag.

| ID | Given | When | Then |
|---|---|---|---|
| AC-081 | a flagged case with a suggested workup | the clinician records results such as a negative HLA-B27, a normal CRP and a negative sacroiliac MRI | the outcome is stored against the case with the date and the recording clinician |
| AC-082 | a recorded negative workup outcome | the case and the worklist are refreshed | the tier is lowered according to the condition pack's rules, the change is shown with the outcome as its reason, and the prior tier remains visible in the case history |
| AC-083 | a recorded workup outcome | the training job is next run | the outcome is not used as training data, since outcomes are stored as data and feed no learning loop in this build |

### US-026: Invite a patient to the product

**Priority:** high

> As a clinician, I want to send a patient an invite link from the product, so that the patient can complete their intake and share their story back to me.

| ID | Given | When | Then |
|---|---|---|---|
| AC-084 | a signed-in clinician | they invite a patient from the worklist or a case | a single-use tokenised invite link is generated for that patient and shown to the clinician for sending |
| AC-085 | an issued invite | the clinician views the patient's row | the invite status reads not yet opened, opened, or intake completed |
| AC-086 | an invite link | it is inspected | the token is unguessable, has a configured expiry, and grants only patient-role access to that one patient's own data |

## EPIC-008: Patient intake, visit prep and sharing

The patient mobile-first experience: a roughly ten-minute symptom intake presented one question per screen with a why we ask explanation, a plain-language visit-prep sheet with patterns worth raising and questions to ask, sharing by unguessable link rendered as a QR code, and the post-workup update telling the patient plainly what was ruled out.

Assumption surfaced here: patient-facing copy never names a likely diagnosis and never shows a tier or score, which is a structural consequence of the FDA non-device CDS posture, not a styling choice.

### US-027: Complete a symptom intake in about ten minutes

**Priority:** critical

> As a patient, I want a short symptom questionnaire, one question at a time, that explains why each question matters, so that I can add the details my records never captured without giving up halfway.

| ID | Given | When | Then |
|---|---|---|---|
| AC-087 | a patient who has entered through an invite link | they start the symptom check | questions are presented one per screen covering the pack's intake items — including stiffness, night pain, NSAID response, alternating buttock pain, family history, body map and self-paid visits — each with a why we ask explanation |
| AC-088 | an intake in progress | the patient leaves and returns later | their answers so far are preserved and they resume at the next unanswered question, with progress shown as a position in the set |
| AC-089 | a completed intake | the answers are stored | each answer becomes a patient-sourced event tagged You told us and is available to the engine and the timeline |
| AC-090 | a representative test run of the intake | completion time is measured | a first-time respondent completes it in about ten minutes or less |

### US-028: Get a plain-language visit-prep sheet

**Priority:** high

> As a patient, I want my story in plain language with patterns worth raising and questions to ask, so that I can be taken seriously in a fifteen-minute appointment.

| ID | Given | When | Then |
|---|---|---|---|
| AC-091 | a patient with a timeline and a completed intake | they open visit prep | they see a plain-language summary of their history, the patterns worth mentioning with the dates and sources behind them, and suggested questions to ask their clinician |
| AC-092 | the visit-prep sheet | an automated guardrail test inspects every string on it | no risk tier, no numeric score and no named likely diagnosis appears, and the test fails if any pack-configured condition name is present in patient-facing copy |
| AC-093 | the visit-prep sheet | the patient chooses to take it with them | it can be printed or saved as a document carrying the synthetic-data notice |

### US-029: Share my case with a clinician by link or QR code

**Priority:** high

> As a patient, I want to share my case with a clinician using a link or a QR code, so that they can see my organised history without me retelling it.

| ID | Given | When | Then |
|---|---|---|---|
| AC-094 | a patient on the visit-prep screen | they choose to share | an unguessable share link is generated and also rendered as a QR code on screen |
| AC-095 | a share link opened by a clinician who signs in with a clinician account | the shared case loads | the clinician sees the full clinician case including the tier, and the access is recorded against the patient's case |
| AC-096 | a share link | it is inspected or revoked | the patient can see that a link is active and can revoke it, after which the link no longer grants access |

### US-030: Receive a clear update after the tests come back

**Priority:** medium

> As a patient whose workup was negative, I want a plain, non-alarming update telling me what was checked and what it means for next steps, so that I am not left anxious or confused after being tested.

| ID | Given | When | Then |
|---|---|---|---|
| AC-097 | a clinician has recorded a negative workup outcome for a patient | the patient opens their app | an update states in plain language which tests were done, that they came back negative, and what the clinician suggested next |
| AC-098 | the post-workup update | an automated guardrail test inspects it | it names no likely diagnosis, shows no tier or score, and contains no wording implying the patient had or escaped a specific disease |
| AC-099 | the post-workup update | it is displayed | the tests and their results appear on the patient's timeline tagged Record with their dates |

## EPIC-009: Accounts, roles and the regulatory split

Email-and-password accounts with two roles — clinician and patient — where the role boundary is what enforces the regulatory split: the risk tier and any underlying score exist only on the clinician side.

Assumptions surfaced here: (a) no SSO, no SMART-on-FHIR and no EHR launch; patients enter via a tokenised invite link that selects a synthetic persona; (b) access is by invitation only and there are no payments, billing, pricing or subscriptions anywhere in the product, so no commercial epic exists for this scope.

### US-031: Sign in as a clinician with an email and password

**Priority:** critical

> As a clinician, I want to sign in with my email address and a password, so that I can work the synthetic worklist under my own identity.

| ID | Given | When | Then |
|---|---|---|---|
| AC-100 | an invited clinician with an account | they sign in with the correct email and password | they reach the worklist, and their decisions are attributed to their account |
| AC-101 | a signed-in clinician | they choose sign out | their session ends immediately and returning to a clinician page requires signing in again |
| AC-102 | a clinician session left idle beyond the configured expiry period | the clinician next acts in the application | the session has expired and they are asked to sign in again |
| AC-103 | a clinician account that an administrator deactivates | the deactivation is saved | any existing sessions for that account stop working and no new sign-in succeeds |
| AC-104 | any stored account | the account store is inspected | passwords are held only as salted hashes, never as recoverable text, and new accounts are set up with a password the user sets at first sign-in as <set-at-first-login> |

### US-032: Enter as a patient through a tokenised invite link

**Priority:** high

> As a invited patient, I want to enter the app through the link my clinician sent me, so that I can see my health story without an onboarding process.

| ID | Given | When | Then |
|---|---|---|---|
| AC-105 | a valid, unexpired invite link | the patient opens it | they are given patient-role access to exactly one synthetic patient's data and are prompted to set a password as <set-at-first-login> if they want to return |
| AC-106 | an expired, revoked or already-consumed invite link | it is opened | access is refused with a plain message and no patient data is shown |
| AC-107 | a signed-in patient | they sign out or their session expires | the session ends and returning requires signing in again |

### US-033: Keep the risk tier on the clinician side only

**Priority:** critical

> As a compliance-minded product owner, I want the tier and any underlying score unreachable by the patient role, so that the product stays inside the non-device clinical decision support posture.

| ID | Given | When | Then |
|---|---|---|---|
| AC-108 | a signed-in patient account | it requests any patient-facing screen or the data behind it | no tier, score, criteria evaluation or suspected-condition name is returned in the response |
| AC-109 | a patient-role account | it requests a clinician screen or clinician data directly | access is refused rather than rendered with sections hidden in the browser |
| AC-110 | an automated role-split test over every patient-facing response in the product | it runs | it finds zero occurrences of a tier value, a score value or a pack condition name, and fails the build otherwise |
| AC-111 | the deployed product | any screen or flow is reviewed | there is no payment, pricing, billing or subscription step anywhere, and access is only ever granted by invitation |

### US-045: Remove the sign-in form from the /start entry screen

**Priority:** medium

> As a demo presenter opening the product, I want the /start screen to show only the two demo entry buttons, with no email or password form, so that the entry screen offers one clear way in and does not present a credential form that is not needed there.

| ID | Given | When | Then |
|---|---|---|---|
| AC-147 | the /start route is opened in a browser | the page renders | no email field, no password field and no submit control for signing in is present anywhere on the screen |
| AC-148 | the /start route is open | the page renders | both demo entry buttons are still shown and the synthetic-data notice is still present on the screen |
| AC-149 | the /start screen with the form removed | the page loads and the user interacts with it | no request is made to POST /api/auth/login from this screen and no credential input state remains in the SPA for this route |
| AC-150 | the /start screen opened in a phone-sized browser window and in a desktop window | the page renders after the form is removed | the remaining buttons and notice are laid out without leftover empty space or horizontal scrolling on either size |

## EPIC-010: The four shipped guardrails

The four non-negotiable guardrails implemented as automated, testable rules rather than written policy: no post-cutoff data reaching scoring or display, no uncited sentence appearing in any generated summary, no risk tier or named likely diagnosis in patient-facing copy, and a synthetic-data banner on every screen. Each runs as a check that can fail the build.

### US-034: Block post-cutoff data from scoring and display

**Priority:** critical

> As a engineering lead, I want an enforced rule that no data dated on or after a patient's cutoff reaches scoring or any screen, so that the lead-time result cannot be an artefact of leakage.

| ID | Given | When | Then |
|---|---|---|---|
| AC-112 | a patient with post-cutoff events in the store | any timeline, case summary, export or evaluation view for that patient is rendered | no post-cutoff event appears, and undated family-history rows are the only exception |
| AC-113 | the automated guardrail suite | it runs across the loaded cohort | it reports zero post-cutoff items in scoring inputs and in rendered output, and a non-zero count fails the build |

### US-035: Block uncited sentences in generated summaries

**Priority:** critical

> As a clinician, I want a verifier that checks every generated sentence against a linked source record, so that I never read a generated claim that no record supports.

| ID | Given | When | Then |
|---|---|---|---|
| AC-114 | a generated clinician summary or patient visit-prep text | the citation verifier runs over it | each factual sentence is matched to a linked source record, and any sentence without a resolvable citation is blocked from publication or visibly flagged as unverified |
| AC-115 | a sentence citing a record that does not exist or belongs to another patient | the verifier runs | the sentence is treated as uncited and handled the same way as a missing citation |
| AC-116 | the automated guardrail suite run over every generated summary in the cohort | it completes | it reports zero published uncited sentences, and a non-zero count fails the build |

### US-036: Keep diagnosis names and risk scores out of patient-facing copy

**Priority:** critical

> As a compliance-minded product owner, I want an automated check over all patient-facing strings, so that the patient side organises data and prompts questions without ever suggesting a disease.

| ID | Given | When | Then |
|---|---|---|---|
| AC-117 | every patient-facing screen, generated text, notification and export in the product | the guardrail check scans them | no tier, no numeric risk value and no condition name from the active pack's prohibited-term list is found |
| AC-118 | a new patient-facing string added to the product or generated by the LLM | the check runs in the build pipeline | a violation fails the build and names the offending string and its location |

### US-037: Show the synthetic-data banner on every screen

**Priority:** critical

> As a demo viewer, I want every screen and export to state that the data is synthetic and not for clinical use, so that nobody mistakes a demo case for a real patient.

| ID | Given | When | Then |
|---|---|---|---|
| AC-119 | any screen in the patient app, the clinician app, the demo replay or the evaluation report | it is rendered | a visible synthetic-data notice is present stating that the data is 100% synthetic and not for clinical use |
| AC-120 | any printable or exported document, including the referral packet and the visit-prep sheet | it is produced | the same notice appears on every page |
| AC-121 | the automated guardrail suite | it visits every route in the application | it reports the banner present on 100% of routes, and a missing banner fails the build |

## EPIC-011: Demo mode: persona picker and odyssey replay

The scripted demo path that ships first: a picker over the six hero personas from heroes.json, an odyssey replay showing what happened versus what would have happened with the lead time, and a performance budget of under sixty seconds from persona selection to a rendered case summary. The six personas are the product's acceptance tests.

Assumption surfaced here: the six static HTML files in design/ are the visual source of truth for these screens.

### US-038: Pick a hero persona to drive the demo

**Priority:** critical

> As a demo presenter, I want to choose any of the six hero personas and land in their story, so that I can walk an investor or advisor through a specific journey without setup.

| ID | Given | When | Then |
|---|---|---|---|
| AC-122 | the ingested heroes.json personas | the presenter opens the persona picker | all six personas are listed with their name and a one-line description of the journey they illustrate |
| AC-123 | a selected persona | the presenter chooses the patient view or the clinician view | that persona's timeline, intake answers and case are loaded as of that persona's cutoff date |
| AC-124 | a persona selected in demo mode | any screen renders | the synthetic-data banner is present and the patient-side guardrails apply exactly as they do outside demo mode |

### US-039: Render a persona from selection to case summary in under sixty seconds

**Priority:** high

> As a demo presenter, I want the full path from picking a persona to a rendered case summary to complete inside sixty seconds, so that the live demo does not stall in front of an audience.

| ID | Given | When | Then |
|---|---|---|---|
| AC-125 | a dataset already loaded by the admin ingest step | the presenter picks a persona and opens the case summary | the timeline, scoring, evidence assembly and summary render complete in under sixty seconds measured end to end |
| AC-126 | a generated summary that has already been produced for a persona | the same persona is opened again | the stored summary is reused so the repeat render is faster than the first |
| AC-127 | the sixty-second budget is exceeded for any of the six personas | the performance check runs | the check fails and reports which stage consumed the time |

### US-040: Watch the odyssey replay with the lead time

**Priority:** high

> As a investor or clinical advisor, I want a side-by-side replay of what happened versus what would have happened with the copilot, so that I can see the diagnostic delay shortened rather than be told about it.

| ID | Given | When | Then |
|---|---|---|---|
| AC-128 | a persona with a simulated diagnosis date | the replay is opened | one track shows the real journey of visits and providers over time and the other shows the point at which the engine would first have reached High or Moderate |
| AC-129 | the replay | it reaches the flag point | the lead time is stated as the interval between the engine's first flag and the simulated diagnosis date, and the facts nobody connected are listed with their sources |
| AC-130 | a persona whose status is Insufficient history | the replay is opened | it shows the point at which the product would have said Insufficient history and what it was missing, rather than showing a flag that never occurred |

### US-041: Hold the six persona pass tests as an automated acceptance suite

**Priority:** critical

> As a engineering lead, I want the six personas' pass tests run automatically, so that a change that breaks the hard journeys is caught before a demo.

| ID | Given | When | Then |
|---|---|---|---|
| AC-131 | the strong-signals persona | the suite runs | the status is High and the first flag is at least two years before their simulated diagnosis date |
| AC-132 | the weak and atypical persona with a negative HLA-B27, a normal CRP and a fibromyalgia label | the suite runs | the status is Moderate or High, the conflicting labels are named, and the summary states that a negative HLA-B27 and a normal CRP do not rule the condition out |
| AC-133 | the osteitis condensans ilii persona and the fibromyalgia persona | the suite runs | neither reaches High, counter-evidence is listed for both, and the alternative explanation is named |
| AC-134 | the side-door persona whose back care was cash-paid | the suite runs after their intake is completed | they are flagged and the uveitis history is cited among the top evidence alongside the intake-reported chiropractic care |
| AC-135 | the sparse-history persona | the suite runs | the status is Insufficient history, no Low tier appears anywhere for them, and a what we still need list is produced |

### US-046: Confirm demo entry and clinician sign-in still work after the form is removed

**Priority:** medium

> As a engineering lead, I want regression coverage over the entry screen, the demo buttons and the existing clinician sign-in route, so that removing the form from /start does not leave a clinician without a way in or break the scripted demo path.

| ID | Given | When | Then |
|---|---|---|---|
| AC-151 | the /start screen with the sign-in form removed | each demo entry button is clicked | the clinician view and the patient view open exactly as they did before the change |
| AC-152 | a clinician with an account and no active session | they sign in on the existing sign-in route | they reach the worklist and their decisions are still attributed to their account |
| AC-153 | the existing automated test suite and the guardrail route sweep | they are run after the form is removed | all existing tests pass and the synthetic-data banner is still reported present on every route including /start |

## EPIC-012: In-app evaluation report

An internal, clinician-side evaluation view that runs the engine across a split and computes the PRD's success metrics in-product, so demo numbers come from the system rather than from a side script.

Assumption surfaced here: this view is the only component permitted to read ground truth from the quarantined labels store, and the test split is reported once per training run.

### US-042: Compute the PRD success metrics inside the product

**Priority:** high

> As a product owner, I want the engine's performance metrics computed and displayed in the application, so that the numbers I quote to investors and advisors come from the shipped product.

| ID | Given | When | Then |
|---|---|---|---|
| AC-136 | a loaded cohort, a persisted model artefact and an operating threshold | the evaluation report is run over a selected split | it reports median lead time versus the simulated diagnosis date measured at the operating threshold, sensitivity per archetype, false-High rate per look-alike group, PPV re-weighted from the cohort's roughly 17% prevalence to roughly 5%, and the share of thin-data patients shown as Insufficient history rather than Low |
| AC-137 | the evaluation report | each metric is displayed | it is shown next to its PRD target with a pass or fail marker, and the split, dataset version, threshold and run date used are stated on the page |
| AC-138 | the false-High metric per look-alike group | it is computed | osteitis condensans ilii, fibromyalgia, HLA-B27-positive mechanical and sports groups are each reported separately rather than only in aggregate |
| AC-139 | the evaluation report is viewed | the page renders | it carries the synthetic-data notice and a stated caveat that these results prove the pipeline works and are not a clinical-accuracy claim |
| AC-140 | a user without the clinician or administrator role | they request the evaluation report | access is refused, since the report contains tiers and scores |

## EPIC-013: One responsive web application and deployment

Both sides ship as a single responsive web application — patient screens mobile-first for phone browsers, clinician screens for desktop — deployed as a managed web app in a US region with configuration supplied as environment settings.

Assumptions surfaced here: (a) no native iOS or Android app is built; (b) PostgreSQL backs the unified event store; (c) SOC 2 and HITRUST certification and any formal FDA submission are out of scope for this release, though the design must not block them.

### US-043: Use the same application on a phone or a desktop

**Priority:** high

> As a user of either side, I want one web application that adapts to my device, so that patients can use a phone browser and clinicians a desktop without separate products.

| ID | Given | When | Then |
|---|---|---|---|
| AC-141 | a patient screen opened in a phone-sized browser window | it renders | the layout matches the mobile designs in design/, is usable with one thumb, and requires no horizontal scrolling |
| AC-142 | a clinician screen opened in a desktop browser window | it renders | the worklist and case summary match the clinician designs in design/ and present the case on one page without nested scrolling panes |
| AC-143 | the deployed product | an app store or native install is sought | none exists, as the product is delivered only as a responsive web application |

### US-044: Deploy and configure the application as a managed web app

**Priority:** medium

> As a platform administrator, I want the application deployed as a managed web app in a US region with configuration supplied as environment settings, so that the proof of concept can be stood up and shown reliably to invited viewers.

| ID | Given | When | Then |
|---|---|---|---|
| AC-144 | a target environment in a US region | the application is deployed | the web application and its PostgreSQL unified-event store start, the health check passes, and the active dataset version is reported on the administrator page |
| AC-145 | environment configuration | it is set | the database connection is supplied as <database-connection-string>, the LLM credential as <llm-api-key>, and no credential value appears in source control, logs or any screen |
| AC-146 | a deployed environment | any unauthenticated request is made to a patient or clinician route | it is refused, since the product is invitation-only and has no public or self-service entry point |
<!-- sdlc:auto:end epics -->
