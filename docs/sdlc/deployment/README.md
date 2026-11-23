# Deployment

> Maintained by QuorQ AI SDLC. Text between `sdlc:auto` markers is regenerated; anything outside them is yours and is kept.

<!-- sdlc:auto:start narrative -->
### DEPLOY-5f7e38c9ddea · approved · source: deployment:5f7e38c9ddea

Version 5f7e38c9ddea of UAT-Feedback (Diagnostic Odyssey Copilot — axSpA Proof of Concept) was deployed and is reported as live. The deployment exposes a hosted frontend and a separately hosted backend API. No further deployment metadata was supplied.

Deployment record (as stated in the input, verbatim fields):
- Status: live
- Version / build id: 5f7e38c9ddea
- Frontend URL: https://p45a9603f83d5.d13el1ykvx8z63.amplifyapp.com
- Backend URL: https://75-101-253-178.sslip.io/apps/45a9603f83d5/

Observations:
- Frontend is served from an AWS Amplify-hosted domain; backend is served from an sslip.io host path scoped to app id 45a9603f83d5. The shared id fragment 45a9603f83d5 appears in both URLs.
- Both endpoints are HTTPS.

Not provided by the input (recorded as gaps, not inferred):
- Deployment date/time and who performed or approved it.
- Target environment label (e.g. UAT vs production) — only "live" was given.
- Release contents: no tickets, stories, or requirements were mapped to this build.
- Post-deployment verification, smoke-test, or monitoring results.
- Rollback/backout procedure and prior version superseded.
- Any credentials or access instructions for the deployed environment (if access control exists, secrets must be supplied out of band, e.g. <set-at-first-login>).
<!-- sdlc:auto:end narrative -->
