"""The baseline test the scaffold ships with.

The platform installs this tree and runs `pytest` against it, so there has to
be something green to run before an agent has written anything -- otherwise the
first real ticket cannot tell a broken change from a repository that never
worked.

The `client` fixture comes from conftest.py and carries a database of its own,
so these tests never touch the one the application is configured with.

Shape per the approved API spec (`GET /health`): `{status, db, cache, queue}`.
`db` and `cache`/`queue` report whether Postgres and Redis answer right now;
the test's own `DATABASE_URL` is the in-memory SQLite the `client` fixture
substitutes, not a real server, and `REDIS_URL` is whatever this sandbox
gives the test process -- so this only pins the shape, not whether either
service happens to be reachable here.
"""

from fastapi.testclient import TestClient


def test_health_reports_ok(client: TestClient) -> None:
    """A failure here means the application does not import or does not start."""
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert set(body) == {"status", "db", "cache", "queue"}
    assert isinstance(body["db"], bool)
    assert isinstance(body["cache"], bool)
    assert isinstance(body["queue"], bool)


def test_the_openapi_document_builds(client: TestClient) -> None:
    """Every generated route contributes to the schema, so a route whose types
    FastAPI cannot resolve fails here rather than on a user's first request."""
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert "/health" in response.json()["paths"]
