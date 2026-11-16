"""Application entrypoint.

Generated from the approved architecture: one router per component that owns
endpoints, one route per endpoint the API spec declares. Every generated route
is a stub that returns a typed placeholder, so the service starts, serves its
OpenAPI document and passes its tests before a single handler is implemented.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import models  # noqa: F401 -- imported so the tables register before create_all
from app.auth import is_authenticated_request
from app.bootstrap import seed_bootstrap_accounts
from app.config import allowed_origins
from app.database import Base, SessionLocal, engine
from app.pack import active_pack_status, log_active_pack
from app.routers import admin, auth, data, ingest_runs, invites, pack
from app.services import configured_services


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """The scaffold ships no migrations, so the tables are created from the models
    when the application starts. Replace this with Alembic before anything holds data
    worth keeping.

    This runs on startup and not at import, so importing the application never opens a
    connection. A test can therefore point `get_db` at a database of its own, and a
    deployment whose `DATABASE_URL` names a server that is not up fails where you can
    read the error, not while pytest collects the files.
    """
    Base.metadata.create_all(bind=engine)
    # BOOTSTRAP_ADMIN_* / SMOKE_TEST_* are unset locally and in the unit-test run, so
    # this seeds nothing there -- see app.bootstrap for exactly what it seeds and why.
    db = SessionLocal()
    try:
        seed_bootstrap_accounts(db)
    finally:
        db.close()
    # One line saying which condition pack is active, or that none is: the app
    # must start cleanly with no pack (AC-022).
    log_active_pack()
    yield


app = FastAPI(
    title="UAT-Feedback",
    description="PRD: Diagnostic Odyssey Copilot \u2014 Proof of Concept",
    version="0.1.0",
    lifespan=lifespan,
)

# The SPA runs on a different origin than the API, so the browser refuses its calls
# unless that origin is allowed here. In development that is the Vite dev server; when
# deployed, the platform injects the frontend's real URL as ALLOWED_ORIGINS (comma
# separated). Point ALLOWED_ORIGINS at the real thing and nothing else has to change.
#
# allow_credentials is False on purpose: this API carries its session in an
# `Authorization: Bearer` header and never in a cookie (a cross-origin cookie is
# dropped unless every attribute is exactly right, and browsers keep tightening
# that). Nothing here needs the credentialed-request mode, and leaving it off
# keeps a wildcard origin from ever being silently combined with cookies.
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins(),
    allow_credentials=False,
    allow_methods=["*"],
    # Authorization is the one header that matters: without it listed, a browser
    # preflight refuses the bearer every call carries.
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def require_authentication(request: Request, call_next):
    """AC-146: every route except the open ones refuses an unauthenticated request.

    Interim, pending the full session-auth story: a request must carry a
    bearer token to get past here at all. The route's own dependency then
    decides whether that token is the shared `API_SECRET_KEY` or a live
    session.
    """
    if request.method == "OPTIONS" or is_authenticated_request(
        request.url.path, request.headers.get("authorization")
    ):
        return await call_next(request)
    return JSONResponse(status_code=401, content={"detail": "Not authenticated"})


app.include_router(auth.router)
app.include_router(data.router)
app.include_router(ingest_runs.router)
app.include_router(admin.router)
app.include_router(pack.router)
app.include_router(invites.router)


@app.get("/health")
def health() -> dict[str, object]:
    """Liveness and readiness: {status, db, cache, queue}, per the API spec.

    Unauthenticated and always reachable, so a probe can tell a process that
    is up from a Postgres or Redis that is down. The active dataset version
    belongs to the administrator page (`GET /api/admin/settings`), not here.
    """
    return {
        "status": "ok",
        **configured_services(),
        # Whether a condition pack is active, and which one. With none, the
        # value is {"active": false, "key": null} (AC-022).
        "condition_pack": active_pack_status(),
    }
