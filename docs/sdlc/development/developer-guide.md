# Developer Guide

> Maintained by QuorQ AI SDLC. Text between `sdlc:auto` markers is regenerated; anything outside them is yours and is kept.

<!-- sdlc:auto:start status -->
_Up to date._
<!-- sdlc:auto:end status -->

<!-- sdlc:auto:start source -->
Generated from commit `adc9fd7` · model `auto`
<!-- sdlc:auto:end source -->

<!-- sdlc:auto:start overview -->
UAT-Feedback is a two-app repository for the 'Diagnostic Odyssey Copilot — axSpA Proof of Concept'. The frontend is a Vite + React 19 single-page app (TypeScript, Tailwind 4, react-router-dom) whose screens render seeded sample data. The backend is a FastAPI service (SQLAlchemy 2, Pydantic 2) that currently exposes only a `GET /health` route. It defaults to a local SQLite database and can be pointed at PostgreSQL through `DATABASE_URL`. `docker-compose.yml` defines Postgres and Redis services for local use. The frontend has an API client seam in `frontend/src/lib/api.ts` but no screen calls the backend yet.
<!-- sdlc:auto:end overview -->

<!-- sdlc:auto:start prerequisites -->
- Node.js 18+ (20+ recommended) and npm, for the frontend
- Python 3.12 (the version the backend Dockerfile uses) and pip, for the backend
- Docker and Docker Compose (optional, for the Postgres/Redis services and the backend image)
<!-- sdlc:auto:end prerequisites -->

<!-- sdlc:auto:start setup -->
1. cd frontend && npm install
2. cd backend && python -m venv .venv
3. cd backend && .venv/bin/pip install -r requirements.txt
4. Optional: copy `.env.example` to `.env` and fill in values; open the file to see which variables it defines, since its contents were not part of this review. Never commit real secrets.
5. Optional, to use Postgres instead of the default SQLite file: docker compose up -d db, then set DATABASE_URL for the backend to a Postgres connection string using the `psycopg` driver, for example postgresql+psycopg://<db-user>:<database-password>@localhost:5432/<db-name>
6. Optional, for end-to-end tests: cd frontend && npm run test:e2e:install
<!-- sdlc:auto:end setup -->

<!-- sdlc:auto:start run -->
| Name | Command | Description |
|---|---|---|
| frontend dev | `cd frontend && npm run dev` | Starts the Vite dev server, which serves on http://localhost:5173 by default. The backend's default CORS allow-list already includes that origin. |
| frontend build | `cd frontend && npm run build` | Bundles the SPA with Vite. It does not typecheck. |
| frontend preview | `cd frontend && npm run preview` | Serves the production build locally. |
| backend dev | `cd backend && .venv/bin/uvicorn app.main:app --reload` | Runs the FastAPI app with auto-reload on http://localhost:8000. Tables are created from the models at startup, and `GET /health` is the only route. The OpenAPI docs are served at /docs. |
| infrastructure | `docker compose up -d db` | Starts only the PostgreSQL 16 container. The compose file also defines `redis-queue` and `redis` services; see Troubleshooting before starting both. |
| backend image | `cd backend && docker build -t uat-feedback-backend .` | Builds the backend image (python:3.12-slim, runs as an unprivileged user, serves uvicorn on port 8000 with a /health healthcheck). |
<!-- sdlc:auto:end run -->

<!-- sdlc:auto:start structure -->
| Path | Purpose |
|---|---|
| `.devcontainer/` | Dev container configuration (devcontainer.json). |
| `.quorq/` | Quorq platform metadata (handoff.json). |
| `backend/` | FastAPI service: Dockerfile, requirements.txt, pytest.ini, ruff.toml. |
| `backend/app/` | Application code: main.py (app, CORS, lifespan, /health), database.py (engine, session, get_db), models.py (SQLAlchemy models, currently none), schemas.py (Pydantic models, including the StubResponse placeholder), services.py. |
| `backend/app/routers/` | Generated routers, one per architecture component that owns endpoints. Currently empty apart from __init__.py. |
| `backend/tests/` | pytest suite with shared fixtures in conftest.py. |
| `backend/tests/integration/` | Integration tests, such as the health check test. |
| `backend/tests/unit/` | Unit tests (package scaffold only). |
| `frontend/` | Vite + React SPA with its package.json, Vite, TypeScript, ESLint, Prettier and Playwright configs. |
| `frontend/e2e/` | Playwright acceptance tests and support helpers. |
| `frontend/src/` | SPA source: main.tsx entry, index.css, test-setup.ts. |
| `frontend/src/lib/` | Shared helpers: api.ts (API client), ui.tsx (components), icons.tsx (icons), navigate.ts. |
<!-- sdlc:auto:end structure -->

<!-- sdlc:auto:start conventions -->
- Backend configuration comes from environment variables: DATABASE_URL (defaults to sqlite:///./app.db) and ALLOWED_ORIGINS (comma-separated; defaults to the local Vite origins http://localhost:5173 and http://127.0.0.1:5173).
- Database sessions are request-scoped via the `get_db` dependency in `app/database.py`. All models inherit `Base` from that module, and `app/main.py` imports `app.models` so tables register before `create_all`.
- Schema creation runs in the FastAPI lifespan at startup, not at import. There are no migrations; the code notes Alembic should replace this before the data matters.
- Generated routes are intended to be stubs returning the typed `StubResponse` until implemented. Only `/health` exists so far.
- Backend linting and formatting use Ruff (`ruff.toml`); backend tests use pytest with `pythonpath = .` and `testpaths = tests`.
- Frontend code is TypeScript/React with the `@` alias mapped to `src/`. It is formatted with Prettier and linted with ESLint. Component tests sit beside components as `src/**/*.{test,spec}.{ts,tsx}`; Playwright specs live in `e2e/`.
- The frontend calls the API through `apiFetch` in `src/lib/api.ts`. The base URL comes from VITE_API_BASE_URL (default http://localhost:8000). A bearer token is taken from the stored session token, otherwise from VITE_API_SECRET_KEY.
- The router is mounted with `basename={import.meta.env.BASE_URL}` so the app can be served from a sub-path.
<!-- sdlc:auto:end conventions -->

<!-- sdlc:auto:start testing -->
| Name | Command | Description |
|---|---|---|
| frontend unit | `cd frontend && npm test` | Runs Vitest component tests (jsdom) under src/; passes when there are no tests. |
| frontend e2e | `cd frontend && npm run test:e2e` | Runs Playwright specs from e2e/. Without E2E_BASE_URL it starts the backend from backend/.venv and builds and previews the frontend on port 4173; with E2E_BASE_URL set it targets that deployment. |
| frontend lint | `cd frontend && npm run lint` | ESLint over the frontend. `npm run lint:fix` applies auto-fixes. |
| frontend format check | `cd frontend && npm run format:check` | Prettier check without writing changes. |
| frontend typecheck | `cd frontend && npm run typecheck` | Runs `tsc --noEmit`; not part of `npm run build`. |
| backend tests | `cd backend && .venv/bin/pytest` | Runs the pytest suite in backend/tests. |
| backend lint | `cd backend && .venv/bin/ruff check .` | Ruff lint of the backend. `ruff format .` formats it. |
<!-- sdlc:auto:end testing -->

<!-- sdlc:auto:start troubleshooting -->
| Problem | Solution |
|---|---|
| `docker compose up` fails with a port 6379 already allocated error. | In docker-compose.yml both `redis-queue` and `redis` publish host port 6379. Start only the services you need (for example `docker compose up -d db`), or change one of the host port mappings. |
| Playwright e2e fails to start the backend because `.venv/bin/python` is not found. | The Playwright config runs the backend with backend/.venv. Create it and install dependencies: cd backend && python -m venv .venv && .venv/bin/pip install -r requirements.txt. Alternatively set E2E_BASE_URL to run against an already-deployed app. |
| The browser blocks frontend requests to the API with a CORS error. | Set ALLOWED_ORIGINS for the backend to the frontend's origin (comma-separated for several). By default only http://localhost:5173 and http://127.0.0.1:5173 are allowed. |
| The backend fails at startup with a database connection error. | Unset DATABASE_URL to use the default local SQLite file (./app.db), or make sure the server named in DATABASE_URL is running, for example `docker compose up -d db`. Connection failures surface at startup because tables are created in the lifespan handler. |
| `pytest` cannot import `app`. | Run pytest from the backend/ directory so pytest.ini's `pythonpath = .` applies. |
| `npm run build` succeeds but `npm run typecheck` reports errors. | This is expected: the build does not typecheck, and generated screens can fail `tsc`, often from untyped `useState({})`. Fix the types incrementally. |
| The frontend entry imports `@/App`, but `src/App.tsx` and `src/screens/` do not appear in the provided file tree. | The frontend README describes both. If they are missing from your checkout, the dev server and build will fail to resolve `@/App`, so confirm the files exist before running. |
| Frontend screens do not show data from the backend. | This is expected: screens render seeded sample data and the backend only exposes /health. `src/lib/api.ts` is the seam for wiring screens to real endpoints. |
<!-- sdlc:auto:end troubleshooting -->
