"""US-037: the synthetic-data notice on every screen and every exported page.

AC-119 the notice is present wherever the app renders data (the patient app,
the clinician app, the demo replay and the evaluation report); AC-120 it is on
every page of every printable or exported document (referral packet,
visit-prep sheet); AC-121 the guardrail suite reports it on 100% of the
application's routes and a missing one fails the build.

Everything here goes through the real API with a real session: the bootstrap
admin signs in through POST /api/auth/login (behaviour rules: that is the only
sign-in), and every id a test needs comes from an API read, never from a row
written by hand.

What the API can prove is the data the screens render and the bytes of the
exports. The rendered DOM of each SPA route is covered by the frontend render
test for the same criteria; this file covers the server side of AC-119, the
whole of AC-120, and the route-coverage report of AC-121 for the API surface.
"""

from __future__ import annotations

import io

import pytest
from fastapi.testclient import TestClient

try:  # pypdf is pinned in backend/requirements.txt; import lazily so a stale
    # environment reports a failing PDF test rather than a collection error
    # that proves nothing about any criterion.
    import pypdf
except ImportError:  # pragma: no cover - environment, not behaviour
    pypdf = None  # type: ignore[assignment]

from tests.integration.conftest import admin_headers
from tests.integration.synthetic_notice import is_notice, payload_carries_notice

# Every API route that answers with data a screen renders. A route that returns
# a screen's content and no notice is exactly the failure AC-119 forbids.
DATA_ROUTES: list[tuple[str, str, dict | None]] = [
    ("GET", "/api/worklist", None),
    ("GET", "/api/patients/me/timeline", None),
    ("GET", "/api/patients/me/updates", None),
    ("GET", "/api/patients/me/visit-prep", None),
    ("GET", "/api/demo/personas", None),
    ("GET", "/api/evaluation/runs/latest", None),
]

PDF_HEADER = b"%PDF-"


def _pdf_pages_text(data: bytes) -> list[str]:
    """The text of each page of a PDF, one string per page."""
    assert pypdf is not None, (
        "pypdf (pinned in backend/requirements.txt) is not installed, so the pages of "
        "the export cannot be read back"
    )
    reader = pypdf.PdfReader(io.BytesIO(data))
    return [page.extract_text() or "" for page in reader.pages]


def _first_persona_key(api: TestClient, headers: dict[str, str]) -> str:
    response = api.get("/api/demo/personas", headers=headers)
    assert response.status_code == 200, (
        f"GET /api/demo/personas returned {response.status_code}: {response.text[:200]}"
    )
    personas = response.json()
    rows = personas["personas"] if isinstance(personas, dict) else personas
    assert rows, "no demo persona is available, so no case can be exported"
    return str(rows[0]["persona_key"])


def _a_patient_id(api: TestClient, headers: dict[str, str]) -> str:
    """A patient id obtained through the API, by opening a demo persona."""
    key = _first_persona_key(api, headers)
    response = api.post(
        f"/api/demo/personas/{key}/open", headers=headers, json={"view": "clinician"}
    )
    assert response.status_code == 200, (
        f"POST /api/demo/personas/{key}/open returned {response.status_code}: {response.text[:200]}"
    )
    body = response.json()
    bundle = body.get("bundle", body)
    patient_id = bundle.get("patient_id") or (bundle.get("case") or {}).get("patient_id")
    assert patient_id, f"the opened persona bundle carries no patient_id: {str(body)[:200]}"
    return str(patient_id)


@pytest.mark.parametrize(("method", "path", "body"), [(m, p, b) for m, p, b in DATA_ROUTES])
def test_ac119_nfr017_every_data_route_carries_the_synthetic_notice(
    api: TestClient, method: str, path: str, body: dict | None
) -> None:
    """AC-119 / NFR-017: whatever a screen renders arrives with a visible notice
    saying the data is synthetic and not for clinical use."""
    headers = admin_headers(api)
    response = api.request(method, path, headers=headers, json=body)

    assert response.status_code == 200, (
        f"{method} {path} returned {response.status_code}: {response.text[:200]}"
    )
    assert payload_carries_notice(response.json()), (
        f"{method} {path} answers with no synthetic-data notice: {response.text[:300]}"
    )


def test_ac119_nfr017_the_demo_replay_carries_the_notice(api: TestClient) -> None:
    """AC-119: the odyssey replay is one of the four named surfaces."""
    headers = admin_headers(api)
    key = _first_persona_key(api, headers)

    opened = api.post(f"/api/demo/personas/{key}/open", headers=headers, json={"view": "patient"})
    assert opened.status_code == 200, (
        f"opening persona {key} returned {opened.status_code}: {opened.text[:200]}"
    )
    assert payload_carries_notice(opened.json()), (
        f"the opened persona carries no synthetic-data notice: {opened.text[:300]}"
    )

    replay = api.get(f"/api/demo/personas/{key}/replay", headers=headers)
    assert replay.status_code == 200, (
        f"the replay returned {replay.status_code}: {replay.text[:200]}"
    )
    assert payload_carries_notice(replay.json()), (
        f"the replay carries no synthetic-data notice: {replay.text[:300]}"
    )


def test_ac119_nfr017_the_evaluation_report_carries_the_notice(api: TestClient) -> None:
    """AC-119: the evaluation report states the numbers come from synthetic data."""
    headers = admin_headers(api)
    response = api.get("/api/evaluation/runs/latest", headers=headers)

    assert response.status_code == 200, (
        f"the evaluation report returned {response.status_code}: {response.text[:200]}"
    )
    assert payload_carries_notice(response.json()), (
        f"the evaluation report carries no synthetic-data notice: {response.text[:300]}"
    )


def test_ac120_nfr017_the_visit_prep_sheet_has_the_notice_on_every_page(api: TestClient) -> None:
    """AC-120 / NFR-017: every page of the exported visit-prep PDF carries it."""
    headers = admin_headers(api)
    response = api.get("/api/patients/me/visit-prep.pdf", headers=headers)

    assert response.status_code == 200, (
        f"the visit-prep export returned {response.status_code}: {response.text[:200]}"
    )
    assert response.content.startswith(PDF_HEADER), "the visit-prep export is not a PDF"

    pages = _pdf_pages_text(response.content)
    assert pages, "the visit-prep PDF has no pages"
    missing = [n for n, text in enumerate(pages, start=1) if not is_notice(text)]
    assert not missing, f"the visit-prep PDF has no synthetic-data notice on pages {missing}"


def test_ac120_nfr017_the_referral_packet_has_the_notice_on_every_page(api: TestClient) -> None:
    """AC-120 / NFR-017: every page of the exported referral packet carries it."""
    headers = admin_headers(api)
    patient_id = _a_patient_id(api, headers)

    response = api.get(f"/api/cases/{patient_id}/referral-packet.pdf", headers=headers)
    assert response.status_code == 200, (
        f"the referral packet returned {response.status_code}: {response.text[:200]}"
    )
    assert response.content.startswith(PDF_HEADER), "the referral packet is not a PDF"

    pages = _pdf_pages_text(response.content)
    assert pages, "the referral packet PDF has no pages"
    missing = [n for n, text in enumerate(pages, start=1) if not is_notice(text)]
    assert not missing, f"the referral packet has no synthetic-data notice on pages {missing}"


def test_ac121_nfr017_every_data_route_is_covered_at_one_hundred_percent(api: TestClient) -> None:
    """AC-121 / NFR-017: the guardrail reports the notice on 100% of the routes it
    visits -- one route without it is a build failure, not a warning."""
    headers = admin_headers(api)

    results: dict[str, bool] = {}
    for method, path, body in DATA_ROUTES:
        response = api.request(method, path, headers=headers, json=body)
        results[f"{method} {path}"] = response.status_code == 200 and payload_carries_notice(
            response.json()
        )

    covered = sum(1 for ok in results.values() if ok)
    percentage = 100.0 * covered / len(results)
    assert percentage == 100.0, (
        f"the synthetic-data notice is present on {percentage:.0f}% of routes; missing on: "
        f"{[name for name, ok in results.items() if not ok]}"
    )
