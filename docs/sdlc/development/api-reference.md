# API Reference

> Maintained by QuorQ AI SDLC. Text between `sdlc:auto` markers is regenerated; anything outside them is yours and is kept.

<!-- sdlc:auto:start endpoints -->
| Method | Path | Handler | Source | Summary |
|---|---|---|---|---|
| POST | /api/admin/ingest-runs | start_ingest_run | `backend/app/routers/ingest_runs.py:87` | — |
| GET | /api/admin/ingest-runs/{run_id} | get_ingest_run | `backend/app/routers/ingest_runs.py:135` | The run's report: its summary and one pass/fail line per file. |
| GET | /api/admin/settings | settings | `backend/app/routers/admin.py:36` | Masked configuration status: never a credential value, only a status. |
| POST | /api/auth/login | login | `backend/app/routers/auth.py:31` | — |
| POST | /api/auth/logout | logout | `backend/app/routers/auth.py:49` | — |
| GET | /api/auth/me | me | `backend/app/routers/auth.py:59` | — |
| GET | /api/cases/{patient_id}/referral-packet.pdf | referral_packet_pdf | `backend/app/routers/data.py:216` | — |
| GET | /api/demo/personas | demo_personas | `backend/app/routers/data.py:156` | — |
| POST | /api/demo/personas/{persona_key}/open | open_persona | `backend/app/routers/data.py:189` | — |
| GET | /api/demo/personas/{persona_key}/replay | persona_replay | `backend/app/routers/data.py:195` | — |
| GET | /api/evaluation/runs/latest | latest_evaluation | `backend/app/routers/data.py:208` | The latest evaluation run. Until the evaluation job exists there is none, |
| GET | /api/patients/me/timeline | my_timeline | `backend/app/routers/data.py:93` | — |
| GET | /api/patients/me/updates | my_updates | `backend/app/routers/data.py:104` | — |
| GET | /api/patients/me/visit-prep | my_visit_prep | `backend/app/routers/data.py:124` | — |
| GET | /api/patients/me/visit-prep.pdf | my_visit_prep_pdf | `backend/app/routers/data.py:129` | — |
| GET | /api/worklist | worklist | `backend/app/routers/data.py:76` | Every patient in the loaded cohort, with the notice (no paging). |
| GET | /health | health | `backend/app/main.py:91` | Liveness and readiness: {status, db, cache, queue}, per the API spec. |
<!-- sdlc:auto:end endpoints -->

<!-- sdlc:auto:start drift -->
**Designed but missing:**

- DELETE /api/patients/me/share-links/{share_id}
- GET /api/admin/extraction-report
- GET /api/admin/jobs/{job_id}
- GET /api/admin/pack
- GET /api/cases/{patient_id}
- GET /api/cases/{patient_id}/timeline
- GET /api/invites/{token}
- GET /api/patients/me/intake
- GET /api/patients/me/share-links
- GET /api/shared/{token}
- POST /api/admin/jobs
- POST /api/admin/users/{user_id}/deactivate
- POST /api/auth/set-password
- POST /api/cases/{patient_id}/decisions
- POST /api/cases/{patient_id}/rescore
- POST /api/cases/{patient_id}/workup-outcomes
- POST /api/evaluation/runs
- POST /api/invites
- POST /api/invites/{token}/accept
- POST /api/patients/me/intake/answers
- POST /api/patients/me/share-links
- PUT /api/admin/pack
<!-- sdlc:auto:end drift -->

<!-- sdlc:auto:start source -->
Generated from commit `822c54c`
<!-- sdlc:auto:end source -->
