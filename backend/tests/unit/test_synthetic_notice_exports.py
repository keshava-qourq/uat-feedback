"""US-037 unit coverage: the notice wording and the exported PDF pages.

AC-119 every payload a screen renders carries the notice; AC-120 every page of
every exported document carries it; AC-121 it is 100% of them, never most.
"""

from __future__ import annotations

import io

import pypdf

from app.notice import SYNTHETIC_DATA_NOTICE, with_notice
from app.pdf import render_pdf
from tests.integration.synthetic_notice import is_notice, payload_carries_notice


def test_ac119_the_notice_says_synthetic_and_not_for_clinical_use() -> None:
    assert is_notice(SYNTHETIC_DATA_NOTICE)


def test_ac119_with_notice_adds_it_to_a_payload_without_dropping_its_data() -> None:
    payload = with_notice({"items": [{"patient_id": "p1"}]})
    assert payload_carries_notice(payload)
    assert payload["items"] == [{"patient_id": "p1"}]


def test_ac120_every_page_of_an_export_carries_the_notice() -> None:
    data = render_pdf([["Page one"], ["Page two"], ["Page three"]])
    assert data.startswith(b"%PDF-")
    pages = pypdf.PdfReader(io.BytesIO(data)).pages
    assert len(pages) == 3
    missing = [n for n, page in enumerate(pages, start=1) if not is_notice(page.extract_text())]
    assert not missing, f"no synthetic-data notice on pages {missing}"


def test_ac121_a_page_with_no_body_text_still_carries_the_notice() -> None:
    pages = pypdf.PdfReader(io.BytesIO(render_pdf([[]]))).pages
    assert is_notice(pages[0].extract_text())
