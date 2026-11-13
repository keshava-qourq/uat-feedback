# API Reference

> Maintained by QuorQ AI SDLC. Text between `sdlc:auto` markers is regenerated; anything outside them is yours and is kept.

<!-- sdlc:auto:start endpoints -->
| Method | Path | Handler | Source | Summary |
|---|---|---|---|---|
| GET | /health | health | `backend/app/main.py:58` | Liveness probe, and the only route here that is not a stub. |
<!-- sdlc:auto:end endpoints -->

<!-- sdlc:auto:start drift -->
**Designed but missing:**

- DELETE /api/patients/me/share-links/{share_id}
- GET /api/admin/extraction-report
- GET /api/admin/ingest-runs/{run_id}
- GET /api/admin/jobs/{job_id}
- GET /api/admin/pack
- GET /api/admin/settings
- GET /api/auth/me
- GET /api/cases/{patient_id}
- GET /api/cases/{patient_id}/referral-packet.pdf
- GET /api/cases/{patient_id}/timeline
- GET /api/demo/personas
- GET /api/demo/personas/{persona_key}/replay
- GET /api/evaluation/runs/latest
- GET /api/invites/{token}
- GET /api/patients/me/intake
- GET /api/patients/me/share-links
- GET /api/patients/me/timeline
- GET /api/patients/me/updates
- GET /api/patients/me/visit-prep
- GET /api/patients/me/visit-prep.pdf
- GET /api/shared/{token}
- GET /api/worklist
- POST /api/admin/ingest-runs
- POST /api/admin/jobs
- POST /api/admin/users/{user_id}/deactivate
- POST /api/auth/login
- POST /api/auth/logout
- POST /api/auth/set-password
- POST /api/cases/{patient_id}/decisions
- POST /api/cases/{patient_id}/rescore
- POST /api/cases/{patient_id}/workup-outcomes
- POST /api/demo/personas/{persona_key}/open
- POST /api/evaluation/runs
- POST /api/invites
- POST /api/invites/{token}/accept
- POST /api/patients/me/intake/answers
- POST /api/patients/me/share-links
- PUT /api/admin/pack
<!-- sdlc:auto:end drift -->

<!-- sdlc:auto:start source -->
Generated from commit `adc9fd7`
<!-- sdlc:auto:end source -->
