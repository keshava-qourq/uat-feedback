# Developer Guide

> Maintained by QuorQ AI SDLC. Text between `sdlc:auto` markers is regenerated; anything outside them is yours and is kept.

<!-- sdlc:auto:start status -->
_Up to date._
<!-- sdlc:auto:end status -->

<!-- sdlc:auto:start source -->
Generated from commit `5f7e38c` · model `auto`
<!-- sdlc:auto:end source -->

<!-- sdlc:auto:start overview -->
UAT-Feedback is a single repository holding two applications for the "Diagnostic Odyssey Copilot" axSpA proof of concept: a FastAPI 0.115 backend in `backend/` and a Vite + React 19 single-page app in `frontend/`. The backend exposes a `/health` probe plus `/api/*` routers for auth and sessions, clinician worklist and case reads, patient timeline/intake/visit-prep, demo personas, patient invites, admin settings, background jobs, ingest runs and the editable condition pack; it uses SQLAlchemy 2 models with Alembic migrations (PostgreSQL 16 in deployment, falling back to a local SQLite file when `DATABASE_URL` is unset), Redis 7 for the read cache and the RQ job queue, S3-or-disk file storage, Anthropic for clue extraction and SendGrid for mail — each of these degrades gracefully when unconfigured. The SPA uses React Router, TanStack Query and Tailwind, stores an opaque bearer token from `POST /api/auth/login` in localStorage and sends it via `Authorization: Bearer` from `src/lib/api.ts`; its screens still largely run on seeded sample data. Tests are pytest (unit + integration) on the backend and Vitest + Playwright on the frontend.
<!-- sdlc:auto:end overview -->

<!-- sdlc:auto:start prerequisites -->
- Python 3.12 (the backend image is python:3.12-slim)
- Node.js with npm (for the Vite 6 / React 19 frontend)
- Docker and Docker Compose (optional, for the PostgreSQL 16 and Redis 7 services in docker-compose.yml)
- libpango-1.0-0 system package if you want WeasyPrint PDF rendering to work locally (the Dockerfile installs it)
<!-- sdlc:auto:end prerequisites -->

<!-- sdlc:auto:start setup -->
1. Clone the repository and change into it.
2. Optional backing services: `docker compose up -d db redis` (PostgreSQL 16 on 5432, Redis 7 on 6379). Without them the backend falls back to a local SQLite file and reports cache/queue unavailable.
3. Create a backend virtualenv: `cd backend && python -m venv .venv`
4. Install backend dependencies: `.venv/bin/pip install -r requirements.txt`
5. Copy `.env.example` and fill in only what you need; every variable has a working local default, so none is required to start. See `ENVIRONMENT.md` and `backend/README.md` for the full table (`DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, `JWT_SECRET_KEY`, `MEDIA_ROOT`, `S3_BUCKET`, `AWS_REGION`, `ANTHROPIC_API_KEY`, `SENDGRID_API_KEY`, `BOOTSTRAP_ADMIN_EMAIL`/`BOOTSTRAP_ADMIN_PASSWORD`, `SMOKE_TEST_EMAIL`/`SMOKE_TEST_PASSWORD`). Use placeholders such as <database-password> and <your-api-key> — never commit a value.
6. Apply migrations: `.venv/bin/alembic upgrade head` (the `users` and `sessions` tables are created by `Base.metadata.create_all` at startup instead).
7. Run the API: `.venv/bin/python -m uvicorn app.main:app --reload` and check http://localhost:8000/health
8. In a second terminal install the frontend: `cd frontend && npm install`
9. Run the SPA: `npm run dev` (it calls http://localhost:8000 unless `VITE_API_BASE_URL` is set at build time).
<!-- sdlc:auto:end setup -->

<!-- sdlc:auto:start run -->
| Name | Command | Description |
|---|---|---|
| api | `cd backend && .venv/bin/python -m uvicorn app.main:app --reload` | Runs the FastAPI service with reload on http://localhost:8000. |
| worker | `cd backend && .venv/bin/python -m app.worker` | Starts the RQ worker entrypoint that runs queued jobs (ingest, dedup check, clue extraction). |
| migrate | `cd backend && .venv/bin/alembic upgrade head` | Applies all Alembic migrations to the configured database. |
| new migration | `cd backend && .venv/bin/alembic revision -m "what changed"` | Creates a new migration revision; the schema is only ever changed this way. |
| services | `docker compose up -d db redis` | Starts PostgreSQL 16 and Redis 7 locally as declared in docker-compose.yml. |
| web dev | `cd frontend && npm run dev` | Starts the Vite dev server for the SPA. |
| web build | `cd frontend && npm run build` | Bundles the app with Vite. It does not typecheck. |
| web preview | `cd frontend && npm run preview` | Serves the production build locally. |
| typecheck | `cd frontend && npm run typecheck` | Runs `tsc --noEmit` over src/ and e2e/. |
| lint (web) | `cd frontend && npm run lint` | ESLint over the whole frontend; `npm run lint:fix` applies fixable issues. |
| format (web) | `cd frontend && npm run format` | Prettier write; `npm run format:check` verifies only. |
| lint (api) | `cd backend && .venv/bin/ruff check .` | Ruff lint over the backend; `.venv/bin/ruff format .` formats it. |
| docker build | `docker build -t uat-feedback-api ./backend` | Builds the API container image (uvicorn on port 8000, with a /health HEALTHCHECK). |
<!-- sdlc:auto:end run -->

<!-- sdlc:auto:start structure -->
| Path | Purpose |
|---|---|
| `backend/` | FastAPI service: requirements.txt, Dockerfile, pytest.ini, ruff.toml, alembic.ini and the app package. |
| `backend/app/` | Application code: main.py (app, CORS, auth middleware, lifespan), config.py, database.py, models.py, schemas.py, sessions.py, auth.py, cache.py, jobs.py, worker.py, storage.py, llm.py, email.py, pdf.py and the domain modules (ingest, dedup, evaluation, labels, invites, provenance). |
| `backend/app/routers/` | One router per component that owns endpoints: auth, data, ingest_runs, admin, pack, invites. |
| `backend/app/engine/` | Scoring engine vocabulary: criteria evaluation, inputs/cutoff handling, tiers. |
| `backend/app/guardrails/` | Guardrail result shape and the leakage guardrail. |
| `backend/app/ingest/` | Dataset ingest job and its source resolution. |
| `backend/app/pack/` | Condition pack as configuration: loader, registry and the shipped YAML packs (packs/axspa.yaml). |
| `backend/alembic/` | Migration environment and versioned migrations (0001–0008). |
| `backend/tests/` | pytest suite split into tests/unit and tests/integration, with shared fixtures and support modules. |
| `backend/scripts/` | Operational scripts, e.g. check_connections.py. |
| `frontend/` | Vite + React SPA: package.json, vite.config.ts, tsconfig.json, playwright.config.ts, eslint config, index.html. |
| `frontend/src/` | App source: main.tsx bootstrap, App.tsx route table and shells, index.css brand tokens, test-setup.ts. |
| `frontend/src/screens/` | One module per approved screen (SignIn, SetPassword, Start, Worklist, CaseSummary, Timeline, MyHealth, InsufficientHistory, Admin) with co-located *.test.tsx. |
| `frontend/src/components/` | Shared components such as SyntheticDataNotice and InvitePatientDialog. |
| `frontend/src/lib/` | api.ts (fetch wrapper, token storage, session-expiry event), ui.tsx, icons.tsx, brand.ts, navigate.ts. |
| `frontend/e2e/` | Playwright acceptance specs and their support helpers. |
| `docs/` | Project documentation, including behaviour-rules.md. |
| `.github/workflows/` | deploy.yml: builds and pushes the API image and publishes the frontend bundle on push to main. |
| `.devcontainer/` | Dev container definition. |
<!-- sdlc:auto:end structure -->

<!-- sdlc:auto:start conventions -->
- One FastAPI router per architecture component, mounted in app/main.py; routes are prefixed `/api/...` and `/health` is the only open, unauthenticated endpoint.
- Auth is an opaque bearer token returned in the login response body and sent as `Authorization: Bearer <token>` — the API never sets a cookie and CORS runs with allow_credentials=False.
- Schema changes go through Alembic migrations only; the `users` and `sessions` tables are the documented exception created by `Base.metadata.create_all`, so nothing may carry a foreign key to them.
- Every config value is read through app/config.py at call time and has a working local default, so the service starts with nothing configured; credential values are never logged or returned (statuses are reported as 'connected'/'not-configured' with the value masked).
- SQLAlchemy models use `Mapped[...] / mapped_column`, string UUID primary keys with a `_uuid()` default, and `JSON().with_variant(JSONB, 'postgresql')` so SQLite and PostgreSQL agree.
- Read payloads are wrapped with `with_notice(...)` so the synthetic-data notice travels with every response, and PDF exports repeat it per page.
- Frontend routes live in a single exported `ROUTES` table in App.tsx; guarded routes are wrapped in `RequireSession`, and the synthetic-data notice is mounted once in the root layout.
- Frontend imports use the `@/` alias for `src/`; component tests sit beside the components they cover as `*.test.tsx` and are scoped to `src/` so Playwright owns `e2e/`.
- Python dependencies are pinned exactly in requirements.txt (including test tooling); Ruff is the single lint/format tool.
<!-- sdlc:auto:end conventions -->

<!-- sdlc:auto:start testing -->
| Name | Command | Description |
|---|---|---|
| backend tests | `cd backend && .venv/bin/python -m pytest` | Runs the unit and integration suites under backend/tests (pythonpath and testpaths come from pytest.ini). |
| backend lint | `cd backend && .venv/bin/ruff check .` | Ruff lint gate for the backend. |
| backend format check | `cd backend && .venv/bin/ruff format --check .` | Verifies backend formatting without rewriting files. |
| frontend unit tests | `cd frontend && npm test` | Runs the Vitest component tests in jsdom (`vitest run --passWithNoTests`). |
| e2e install | `cd frontend && npm run test:e2e:install` | Downloads the Chromium browser Playwright needs. |
| e2e tests | `cd frontend && npm run test:e2e` | Runs the Playwright specs in e2e/. Without E2E_BASE_URL it boots the backend (backend/.venv uvicorn) and a built preview of the SPA; with E2E_BASE_URL set it runs against that deployed URL. |
<!-- sdlc:auto:end testing -->

<!-- sdlc:auto:start troubleshooting -->
| Problem | Solution |
|---|---|
| `pytest` cannot `import app`. | Run it from the `backend/` directory so pytest.ini's `pythonpath = .` applies: `cd backend && .venv/bin/python -m pytest`. |
| `/health` reports cache and queue as unavailable. | That is the default with no Redis. Start it with `docker compose up -d redis` and set `REDIS_URL` to your instance. |
| Admin settings show the LLM as 'not-configured' and extraction returns structured-only output. | Set `ANTHROPIC_API_KEY` (or the generic `LLM_API_KEY`) to <your-api-key> as deployment configuration; it is never committed and the app degrades deliberately when absent. |
| Browser calls from the SPA are blocked by CORS. | Set `ALLOWED_ORIGINS` on the API to the SPA's origin (comma separated). It defaults to the Vite dev server only. |
| `npm run build` succeeds but deployment or `tsc` fails. | `vite build` does not typecheck. Run `npm run typecheck` and fix the reported errors (commonly untyped `useState({})` later read for named fields). |
| WeasyPrint import or PDF rendering fails locally. | It needs the native Pango stack; install libpango-1.0-0 (the Dockerfile does) or rely on the unit tests that mock the renderer. |
| `POST /api/admin/ingest-runs` returns 409 'already in progress' though nothing is running. | A run row is only treated as live while its job is on the queue; bring Redis back up or wait for the 30-minute stale window, after which the abandoned row is marked failed automatically. |
| Cannot sign in locally — no accounts exist. | An empty `users` table is the correct local state. Set `BOOTSTRAP_ADMIN_EMAIL` and `BOOTSTRAP_ADMIN_PASSWORD` (use <set-at-first-login> style placeholders in docs, a real value only in your untracked environment) and restart; seeding is idempotent and never overwrites an existing account. |
| `docker compose up` fails with a port conflict on 6379. | The `redis` and `redis-queue` services both publish 6379; start only one of them, or remap the published port before bringing both up. |
<!-- sdlc:auto:end troubleshooting -->
