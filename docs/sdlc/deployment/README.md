# Deployment

> Maintained by QuorQ AI SDLC. Text between `sdlc:auto` markers is regenerated; anything outside them is yours and is kept.

<!-- sdlc:auto:start narrative -->
### DEPLOY-6f6de49208ab · approved · source: deployment:6f6de49208ab

Version 6f6de49208ab of the Diagnostic Odyssey Copilot axSpA proof of concept is deployed and reported live. The deployment exposes a frontend hosted on AWS Amplify and a backend service reached over HTTPS via an sslip.io hostname. No date, owner, environment label or verification outcome was supplied with this deployment record.

Deployment record as given:
- Status: live
- Version / build identifier: 6f6de49208ab
- Frontend URL: https://p45a9603f83d5.d13el1ykvx8z63.amplifyapp.com (AWS Amplify-hosted domain)
- Backend URL: https://75-101-253-178.sslip.io/apps/45a9603f83d5/ (HTTPS, sslip.io hostname resolving to host 75.101.253.178, app path segment 45a9603f83d5)

Observations:
- The frontend subdomain (p45a9603f83d5) and the backend app path (45a9603f83d5) share the same identifier fragment, indicating the two endpoints belong to the same deployed app instance.
- The source status value is literally "live"; it is recorded here as 'approved' because the schema has no 'live' value. The original wording is preserved in this field.

Not stated in the input and therefore not documented:
- Deployment date/time, deploying agent or person, and approver.
- Target environment name (e.g. UAT, staging, production) — the project name references UAT but the deployment input does not state the environment.
- Release notes, migration steps, configuration or secrets handling, and any credentials (none are recorded here; any required value is set externally, e.g. <set-at-first-login>).
- Smoke-test / post-deploy verification results, monitoring or alerting setup, and rollback or previous-version information.
- Mapping to specific requirement keys (US-001 … US-044); the deployment input provides no traceability data, so no related_ids are asserted.
<!-- sdlc:auto:end narrative -->
