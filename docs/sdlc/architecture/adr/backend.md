<!-- sdlc:auto:start adr -->
# ADR-0002: Use FastAPI 0.115 for Backend

Status: Accepted  
Date: 2026-11-13

## Context and Problem Statement

Which Backend technology does the project use? Decided in architecture v1.

## Considered Options

- FastAPI 0.115
- Django REST Framework
- Flask
- Node.js with NestJS

## Decision Outcome

Chosen option: FastAPI 0.115, because The scoring engine, leakage-safe cutoff logic and evaluation metrics already exist in Python, so they move into the FastAPI 0.115 service as modules rather than being re-implemented and re-validated. The same image runs the API and the RQ worker, so ingest, de-duplication, extraction, training and evaluation share the exact engine code the live case path uses — no second implementation to drift. Pydantic response models are where the role split and the guardrails are enforced, which gives one place to prove that no tier or score leaves on a patient-role response.

## Consequences

FastAPI gives no admin UI, so the pack editor, ingest report and settings pages are hand-built React screens. Long jobs must not run in the request thread, which is exactly why ingest, extraction, training and evaluation are pushed onto the Redis queue; the API keeps only the fast read paths.
<!-- sdlc:auto:end adr -->