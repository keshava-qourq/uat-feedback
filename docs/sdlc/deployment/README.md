# Deployment

> Maintained by QuorQ AI SDLC. Text between `sdlc:auto` markers is regenerated; anything outside them is yours and is kept.

<!-- sdlc:auto:start narrative -->
### DEPLOY-fabe3d2e3293 · approved · source: deployment:fabe3d2e3293

Version fabe3d2e3293 of the Diagnostic Odyssey Copilot axSpA proof of concept is deployed and reported live. The frontend is served from an AWS Amplify-hosted URL and the backend from an sslip.io-mapped application endpoint. No failure or rollback was reported for this attempt.

Deployment record as stated in the input:

- Status: live
- Version: fabe3d2e3293
- Frontend URL: https://p45a9603f83d5.d13el1ykvx8z63.amplifyapp.com
- Backend URL: https://75-101-253-178.sslip.io/apps/45a9603f83d5/

Observations:
- Frontend and backend share the application identifier 45a9603f83d5 across both URLs.
- Frontend hosting is an AWS Amplify app domain; backend is exposed over HTTPS via an sslip.io hostname mapped to 75.101.253.178.

Not provided in the input (recorded as gaps, not inferred):
- Deployment date/time and who performed or approved it.
- Target environment label (e.g. UAT vs production) and any promotion sequence.
- Build/release notes, migration steps, or configuration changes applied.
- Post-deployment smoke tests, health checks, or verification results.
- Rollback procedure or previous version superseded by fabe3d2e3293.
- Monitoring, alerting, or access-control details for the deployed endpoints.
<!-- sdlc:auto:end narrative -->
