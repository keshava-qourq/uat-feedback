<!-- sdlc:auto:start adr -->
# ADR-0001: Use React 19 for Frontend

Status: Accepted  
Date: 2026-11-13

## Context and Problem Statement

Which Frontend technology does the project use? Decided in architecture v1.

## Considered Options

- React 19
- Vue 3
- SvelteKit
- Angular

## Decision Outcome

Chosen option: React 19, because One React 19 codebase carries both sides of this product: the one-question-per-screen intake and timeline rendered mobile-first, and the dense clinician worklist and one-page case summary on desktop. Routes are split by role so patient screens are compiled from serialisers that never receive a tier, and the demo pieces — persona picker, odyssey replay animation, evidence chips that drill into the timeline, QR share — are all ordinary React components. The build reads the API hostname from VITE_API_BASE_URL and keeps the opaque session token in memory/storage, sending it as Authorization: Bearer.

## Consequences

A single SPA means the clinician bundle and the patient bundle share a build, so route-level code splitting is needed to keep the mobile first load small, and the synthetic-data banner must be a layout-level component so the guardrail route sweep finds it on every route rather than relying on each page to remember it.
<!-- sdlc:auto:end adr -->