# Deployment

> Maintained by QuorQ AI SDLC. Text between `sdlc:auto` markers is regenerated; anything outside them is yours and is kept.

<!-- sdlc:auto:start narrative -->
### DEPLOY-a3e24c10b570 · approved · source: deployment:a3e24c10b570

Deployment of version a3e24c10b570 of the Diagnostic Odyssey Copilot axSpA proof of concept. The deployment is reported as live. The application is served as a split frontend/backend deployment, with the frontend hosted on AWS Amplify and the backend exposed under an sslip.io host path scoped to the app id 45a9603f83d5.

Recorded facts (as stated in the deployment input):
- Status: live
- Version / build identifier: a3e24c10b570
- Frontend URL: https://p45a9603f83d5.d13el1ykvx8z63.amplifyapp.com (AWS Amplify-hosted)
- Backend URL: https://75-101-253-178.sslip.io/apps/45a9603f83d5/ (HTTPS, sslip.io hostname, app-scoped path)
- Both endpoints share the app identifier fragment 45a9603f83d5, indicating frontend and backend belong to the same deployed application instance.

Not stated in the input and therefore not documented:
- Deployment date/time and duration
- Target environment label (e.g. UAT, staging, production)
- Who performed or approved the deployment
- Build/CI pipeline, migration steps, or configuration changes applied
- Smoke-test or post-deployment verification results
- Rollback plan or prior/superseded deployment versions
- Traceability to specific requirement keys (US-001 … US-044); the input provides no mapping between this release and any requirement.

Any credentials required to access these endpoints are not recorded here; use the values issued through the project's secret store (e.g. <deployment-access-token>).
<!-- sdlc:auto:end narrative -->
