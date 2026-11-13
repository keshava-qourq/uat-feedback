<!-- sdlc:auto:start adr -->
# ADR-0003: Use PostgreSQL 16 for Database

Status: Accepted  
Date: 2026-11-13

## Context and Problem Statement

Which Database technology does the project use? Decided in architecture v1.

## Considered Options

- PostgreSQL 16
- MySQL 8
- MongoDB
- SQLite

## Decision Outcome

Chosen option: PostgreSQL 16, because The unified event model is one row per fact per source with provenance on every row — a relational table — and the product's central promise, that every flag links back to the record that produced it, is a join from evidence_items to events or note_findings. PostgreSQL 16 holds the 572k events, 167k truth rows and 40k notes and indexes them by patient and event_time so a persona renders inside the 60-second budget, its built-in full-text search covers finding wording inside notes with no separate search service, JSONB holds the condition pack and metric payloads, and schema-level grants are what physically keep the ground-truth labels away from the engine role.

## Consequences

Keeping the eval schema unreadable to the app role means two database roles and a migration discipline that never grants the app access by accident; a grant audit belongs in the guardrail suite. Bulk loading 572k rows wants COPY-style chunked inserts in the worker rather than per-row ORM writes, and the generated PDFs and dataset files stay in S3 rather than the database.
<!-- sdlc:auto:end adr -->