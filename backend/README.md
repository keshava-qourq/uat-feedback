# API

FastAPI 0.115 service for the Diagnostic Odyssey Copilot (axSpA proof of concept).

Run it:

```bash
.venv/bin/python -m uvicorn app.main:app --reload
```

It starts with nothing configured: the database falls back to a local SQLite
file, the cache and queue report themselves unavailable, and `GET /health`
tells you which backing services are actually reachable.

## Checks

```bash
.venv/bin/python -m pytest        # unit and integration tests
.venv/bin/ruff check .            # lint
.venv/bin/ruff format --check .   # formatting
```

## Migrations

The schema is only ever changed through a migration -- never by editing a
model and restarting.

```bash
.venv/bin/alembic upgrade head
.venv/bin/alembic revision -m "what changed"
```

`alembic/` and `alembic.ini` are copied into the image, so the same command
runs against the deployed database and against the worker container.

Two tables are the exception and are still created by `Base.metadata.create_all`
at startup: `users` and `sessions`. Nothing else may carry a foreign key to
them for that reason -- see the note in `app/models.py`.

## Environment

Every variable below is read with a working local default: none is required to
start. No value is ever written into this repository.

### Platform

| Variable | Holds |
|---|---|
| `ALLOWED_ORIGINS` | The SPA's origin for CORS, comma separated. Defaults to the Vite dev server. |
| `SECRET_KEY` | The shared API bearer the generated frontend sends. **Public** -- it is baked into the frontend bundle, so it signs nothing. |
| `JWT_SECRET_KEY` | Private. Hashes session and link tokens. Never `SECRET_KEY`. |
| `MEDIA_ROOT` | A writable directory that survives redeploys; the disk backend for `app.storage` when S3 is not configured. |

### Backing services

See `../ENVIRONMENT.md` for the connection examples.

| Variable | Holds |
|---|---|
| `DATABASE_URL` | SQLAlchemy URL of PostgreSQL 16 (`postgresql+psycopg://...`). |
| `REDIS_URL` | Redis 7, used as both the read cache and the job queue. |
| `S3_BUCKET`, `AWS_REGION` | The project's S3 bucket. Unset locally: files go under `MEDIA_ROOT`. |
| `ANTHROPIC_API_KEY` | Claude, for clue extraction and cited text. `LLM_API_KEY` is accepted as the generic name for the same credential. Supplied as deployment configuration only, never committed; absent, the app degrades to structured-only output and reports "not-configured". |
| `SENDGRID_API_KEY` | Outbound invite and password-set mail. Absent: an invite is still issued, just not emailed. |

### Seeded accounts

Set by the platform on the deployed API. Seeded once at startup, idempotently
-- an account that already has that email is left exactly as it is, password
included. With a pair unset, nothing is seeded: an empty `users` table is the
correct state locally and in the test run.

| Variable | Holds |
|---|---|
| `BOOTSTRAP_ADMIN_EMAIL` | Email of the first administrator. |
| `BOOTSTRAP_ADMIN_PASSWORD` | That administrator's password. Seeded with the highest role, `admin`. |
| `SMOKE_TEST_EMAIL` | Email of the smoke-test account. |
| `SMOKE_TEST_PASSWORD` | Its password. Seeded with the lowest role, `patient`. |

## Layout

| Path | What it is |
|---|---|
| `app/config.py` | Every environment setting, read at call time, each with a local default. |
| `app/database.py` | Engine, session factory, `get_db`. |
| `app/models.py` | SQLAlchemy models for the approved data model. |
| `app/sessions.py` | Opaque bearer sessions: issue, verify, refresh, revoke. |
| `app/cache.py` | The Redis read cache. Every key is disposable. |
| `app/jobs.py` | The RQ job queue: enqueue and status. |
| `app/worker.py` | The worker entrypoint (`python -m app.worker`). |
| `app/storage.py` | Files: S3 when `S3_BUCKET` is set, `MEDIA_ROOT` otherwise. |
| `app/llm.py` | The Anthropic seam, and whether it is configured. |
| `app/email.py` | The SendGrid seam. Never a blocker, never a fake. |
| `app/pack/` | The condition pack as configuration; resolves the active version. |
| `app/engine/` | The scoring engine's shared vocabulary (tiers). |
| `app/guardrails/` | The shape the four guardrails report in. |

## Sessions, not cookies

The SPA and the API are on different origins once deployed. `POST
/api/auth/login` returns an opaque token **in the response body**; the SPA
stores it and sends `Authorization: Bearer <token>` on every later call.
Nothing here sets a cookie: a cross-origin browser drops one unless every
attribute is exactly right, and browsers keep restricting them further.
