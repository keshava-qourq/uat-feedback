# Deployment

> Maintained by QuorQ AI SDLC. Text between `sdlc:auto` markers is regenerated; anything outside them is yours and is kept.

<!-- sdlc:auto:start narrative -->
### DEPLOY-f1ada6c52759 · approved · source: deployment:f1ada6c52759

Version f1ada6c52759 of the Diagnostic Odyssey Copilot (axSpA PoC) is deployed and reported live. The frontend is served from an AWS Amplify-hosted URL and the backend from an sslip.io host under an app-specific path. No deployment date, approver, or release notes were provided in the input.

Deployment record (as provided):
- Status: live
- Version / build identifier: f1ada6c52759
- Frontend URL: https://p45a9603f83d5.d13el1ykvx8z63.amplifyapp.com
- Backend URL: https://75-101-253-178.sslip.io/apps/45a9603f83d5/

Observations:
- Both endpoints are served over HTTPS.
- The frontend host pattern (*.amplifyapp.com) indicates AWS Amplify hosting; the backend is exposed via an sslip.io hostname mapped to IP 75.101.253.178, routed by an app path segment (45a9603f83d5) that matches the frontend subdomain prefix.

Not stated in the input (recorded as gaps, not assumed):
- Deployment date/time and who performed or approved it.
- Target environment label (e.g. dev/staging/production) and whether this is the first or a repeat deployment attempt.
- Release notes, included tickets, or the requirements/stories covered by this version — therefore no related_ids are linked.
- Smoke-test or post-deployment verification results, monitoring, rollback procedure, and any credentials/configuration handling.

Traceability note: no mapping from this deployment to requirement keys US-001..US-044 was supplied, so none is asserted here.
<!-- sdlc:auto:end narrative -->
