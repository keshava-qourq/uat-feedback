# API Reference

> Maintained by QuorQ AI SDLC. Text between `sdlc:auto` markers is regenerated; anything outside them is yours and is kept.

<!-- sdlc:auto:start endpoints -->
| Method | Path | Handler | Source | Summary |
|---|---|---|---|---|
| POST | /api/admin/ingest-runs | start_ingest_run | `backend/app/routers/ingest_runs.py:161` | — |
| GET | /api/admin/ingest-runs/{run_id} | get_ingest_run | `backend/app/routers/ingest_runs.py:207` | The run's report: its summary and one pass/fail line per file. |
| POST | /api/admin/jobs | start_job | `backend/app/routers/admin.py:78` | — |
| GET | /api/admin/jobs/{job_id} | get_job | `backend/app/routers/admin.py:109` | — |
| GET | /api/admin/pack | get_pack | `backend/app/routers/pack.py:124` | — |
| PUT | /api/admin/pack | put_pack | `backend/app/routers/pack.py:133` | — |
| GET | /api/admin/settings | settings | `backend/app/routers/admin.py:45` | Masked configuration status: never a credential value, only a status. |
| POST | /api/admin/users | create_user | `backend/app/routers/admin.py:132` | — |
| POST | /api/admin/users/{user_id}/deactivate | deactivate_user | `backend/app/routers/admin.py:167` | — |
| POST | /api/auth/login | login | `backend/app/routers/auth.py:53` | — |
| POST | /api/auth/logout | logout | `backend/app/routers/auth.py:68` | — |
| GET | /api/auth/me | me | `backend/app/routers/auth.py:78` | — |
| POST | /api/auth/set-password | set_password | `backend/app/routers/auth.py:83` | — |
| POST | /api/cases/{patient_id}/decisions | record_decision | `backend/app/routers/data.py:163` | AC-100: the decision stores the acting user_id from the verified session. |
| GET | /api/cases/{patient_id}/referral-packet.pdf | referral_packet_pdf | `backend/app/routers/data.py:417` | — |
| GET | /api/cases/{patient_id}/timeline | case_timeline | `backend/app/routers/data.py:386` | One patient's stored events, each with its provenance and note text. |
| GET | /api/demo/personas | demo_personas | `backend/app/routers/data.py:334` | — |
| POST | /api/demo/personas/{persona_key}/open | open_persona | `backend/app/routers/data.py:367` | — |
| GET | /api/demo/personas/{persona_key}/replay | persona_replay | `backend/app/routers/data.py:373` | — |
| GET | /api/evaluation/runs/latest | latest_evaluation | `backend/app/routers/data.py:406` | The latest evaluation report: sensitivity and PPV over the loaded |
| POST | /api/invites | create_invite | `backend/app/routers/invites.py:78` | AC-084: a clinician or admin issues one single-use invite for one patient. |
| DELETE | /api/invites/{invite_id} | revoke_invite | `backend/app/routers/invites.py:120` | NFR-009: a clinician revokes an issued invite; the link stops working. |
| GET | /api/invites/{token} | open_invite | `backend/app/routers/invites.py:103` | Unauthenticated: the token is the credential, and this records the open. |
| POST | /api/invites/{token}/accept | accept | `backend/app/routers/invites.py:132` | Consume the invite and sign the patient in, bound to that one patient. |
| GET | /api/patients/me/intake | my_intake | `backend/app/routers/data.py:236` | AC-085: what the invited patient still has to answer. |
| POST | /api/patients/me/intake/answers | record_intake_answer | `backend/app/routers/data.py:258` | Store one intake answer; the last one marks the intake complete (AC-085). |
| GET | /api/patients/me/timeline | my_timeline | `backend/app/routers/data.py:199` | — |
| GET | /api/patients/me/updates | my_updates | `backend/app/routers/data.py:282` | — |
| GET | /api/patients/me/visit-prep | my_visit_prep | `backend/app/routers/data.py:302` | — |
| GET | /api/patients/me/visit-prep.pdf | my_visit_prep_pdf | `backend/app/routers/data.py:307` | — |
| GET | /api/worklist | worklist | `backend/app/routers/data.py:135` | Every patient in the loaded cohort, with the notice (no paging). |
| GET | /health | health | `backend/app/main.py:107` | Liveness and readiness: {status, db, cache, queue}, per the API spec. |
<!-- sdlc:auto:end endpoints -->

<!-- sdlc:auto:start drift -->
**Designed but missing:**

- DELETE /api/patients/me/share-links/{share_id}
- GET /api/admin/extraction-report
- GET /api/cases/{patient_id}
- GET /api/patients/me/share-links
- GET /api/shared/{token}
- POST /api/cases/{patient_id}/rescore
- POST /api/cases/{patient_id}/workup-outcomes
- POST /api/evaluation/runs
- POST /api/patients/me/share-links

**Code only:**

- DELETE /api/invites/{invite_id}
- POST /api/admin/users
<!-- sdlc:auto:end drift -->

<!-- sdlc:auto:start source -->
Generated from commit `f1ada6c`
<!-- sdlc:auto:end source -->
