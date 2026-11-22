# Behaviour rules

How this app behaves where the requirements and the API contract do not say. QA's
tests and the code both follow these rules. The platform keeps this file: the first
rules come from the contract and the code, and each later rule from a decision made
when a test and the code disagreed.

- Sign-in is only via POST /api/auth/login with email and password; there is no self-service sign-up, so every account exists because an admin, a clinician invite, or a patient invite-accept created it.
- Login compares the email case-insensitively (the column is citext) and returns 401 for either a wrong password or a deactivated account without revealing which, so no test can distinguish the two from the response alone.
- On success, login returns an opaque bearer token in the JSON body (never a cookie); the SPA sends it as `Authorization: Bearer <token>` on every later call and the server never issues Set-Cookie.
- Signing in again does not end the previous session: each successful login inserts a new `sessions` row, so the same user can hold several valid tokens at once from different devices or tabs.
- A session stays valid until its idle timeout elapses with no authenticated request, until `POST /api/auth/logout` revokes it, or until `POST /api/admin/users/{id}/deactivate` revokes all of that user's sessions; there is no separate fixed-length absolute expiry.
- Every authenticated request against a live session refreshes `last_seen_at` and pushes `idle_expires_at` forward from the current time, so activity keeps a session alive indefinitely while idling for long enough lets it lapse.
- Logout revokes only the session tied to the token presented in that call; the user's other open sessions on other devices keep working.
- Deactivating a user revokes every one of that user's sessions immediately and makes every later login attempt for that account fail even with the correct password.
- Every error response shares one shape, `{"detail": ...}` (a string for most errors, FastAPI's list-of-objects form for validation errors), with no other top-level fields.
- Not signed in (missing, malformed, expired or revoked bearer token) returns 401.
- Not allowed (an authenticated token of the wrong role, e.g. a patient token on a clinician or admin route) returns 403.
- Not found (an unknown patient id, user id, job id, run id or token) returns 404.
- Invalid input (missing required fields, wrong types, values outside an enumerated set such as `decision` or `kind`) returns 422 with FastAPI's standard validation-error body.
- A conflict (accepting an already-consumed or revoked invite, resolving an already-revoked share link, re-running a job that already finished) returns 409.
- No listing endpoint (`/api/worklist`, `/api/patients/me/share-links`, timelines, replay tracks) takes page or limit parameters in the contract, so each returns its entire result set in one response rather than paging.
- Timeline, replay and updates lists are returned in ascending chronological order by their date or time field, oldest first, matching the narrative they represent.
- Share-link and invite listings are returned newest-first by creation time, so the item a user most recently created or issued appears first.
- Every stored and returned timestamp is UTC (`timestamptz`); API responses serialise it as ISO-8601 with an explicit UTC offset, never a bare local time.
- Plain `date` fields (cutoff_date, reachable_history_start, item_date, expires_at-adjacent dates) carry no time-of-day or zone component, and "today" and all cutoff comparisons are computed from the UTC calendar date because no per-user time zone is stored anywhere in the data model.
- A case's cutoff_date is an inclusive boundary against future knowledge: the timeline, case view and referral packet never include an item dated on or after that cutoff, so advancing the cutoff by one day is the only way an item dated that day becomes visible.
- Every primary key across the schema is a server-generated UUID; no endpoint accepts a client-supplied id when creating a row.
- Email addresses are the one case-insensitive, globally-unique identifier in the system (citext unique on `users.email`); every other text identifier compared for matching (display_name, dataset_patient_id, pack_key, persona_key) is compared case-sensitively.
- Invite, share-link and password-reset tokens are opaque random strings distinct from UUIDs, are never persisted or re-displayed in plaintext once issued, and the database stores only their salted hash, so no endpoint can be used to recover or list a live token's value.
- Each invite and share-link token is scoped to exactly one patient and one granted role and is refused with the same error once it is consumed, revoked, or past its `expires_at`, regardless of which of those three states caused it.
- Tests create every user, patient, invite, share link, and case fixture they need by calling the real API (ingest/admin seeding, invite issue-and-accept, demo persona open) rather than inserting rows directly, and each test issues its own invite, patient and session so concurrent tests never share a token, patient, or demo persona state.
- The acceptance criteria and behaviour rules only require fixtures to be built through the real API — they do not require one full ingest run per test — while NFR-021's one-run-at-a-time ingest and the shared sandbox database are higher sources than the test's convenience, so the helper must change: build the patient cohort once per module (module-scoped, reused by all tests) and tolerate an alread
- The behaviour rules say fixtures must be built through the real API but explicitly do not require an ingest run per test, and NFR-021's serialised ingest plus the shared sandbox database outrank the test's convenience, so the helper is wrong: it must take two patient ids from the cohort already visible on GET /api/worklist and only attempt an ingest when no cohort exists, treating a 409 or an alre
- The test and the code disagree on whether a rendered case read must state the patient's evaluation cutoff: NFR-013/AC-029 require the leakage guarantee to be proven by an automated check across the whole loaded cohort, and the behaviour rules list cutoff_date among the plain date fields API responses carry (and AC-010 expressly allows eval_cutoff_date to be read operationally), so the backend is w
