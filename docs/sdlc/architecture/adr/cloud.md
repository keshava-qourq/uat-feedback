<!-- sdlc:auto:start adr -->
# ADR-0004: Use AWS for Cloud

Status: Accepted  
Date: 2026-11-13

## Context and Problem Statement

Which Cloud technology does the project use? Decided in architecture v1.

## Considered Options

- AWS
- Google Cloud Platform
- Microsoft Azure
- Render

## Decision Outcome

Chosen option: AWS, because A standard managed web app in a US region: App Runner for the FastAPI service, an ECS Fargate task for the RQ worker and the redis:7-alpine container, Amazon RDS for PostgreSQL 16, S3 for the dataset files and generated PDFs, Secrets Manager for the credentials. It is the environment clinical advisors and investors expect to hear named, and the one with the clearest path to the HIPAA-eligible configuration and SOC 2 work deliberately deferred here, so today's PoC does not need rebuilding when real patient data eventually arrives.

## Consequences

More moving parts than a single-container host — a VPC, two services, a managed database and a bucket — which is extra setup for an invitation-only PoC. Running Redis as a container rather than ElastiCache keeps cost down for the demo but means no managed failover, acceptable because both cache and queue contents are rebuildable from Postgres and the dataset.
<!-- sdlc:auto:end adr -->