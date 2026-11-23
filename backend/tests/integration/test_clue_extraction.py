"""US-015-4: the clue extractor and its report, proved against the running API
(AC-049, AC-050, AC-051, AC-052, NFR-006).

Everything goes through the real HTTP API against the sandbox's PostgreSQL and
Redis: the bootstrap admin signs in through POST /api/auth/login (the only
sign-in), the cohort is loaded once for this module through
POST /api/admin/ingest-runs over a fixture drop whose note text the test knows
sentence by sentence, and the extractor is run exactly as the contract says a
screen runs it -- POST /api/admin/jobs {"kind": "extraction"} followed by
GET /api/admin/jobs/{job_id}. No row is written by hand.

Each assertion names the note, the clue and the patient involved, so a failure
here reads as a defect report.
"""

from __future__ import annotations

import os
import secrets
import uuid
from typing import Any

from fastapi.testclient import TestClient

from tests.integration.conftest import admin_headers
from tests.integration.extraction_support import (
    EXTRACTION_REPORT,
    JOBS,
    case_payloads,
    clue_of,
    extraction_cohort,
    extraction_report,
    extraction_run,
    findings,
    note_ref_of,
    objects,
    patient_uuids,
    quote_of,
    start_extraction,
    strings,
    wait_for_job,
)
from tests.integration.fixtures_extraction import REPORT_KEYS, TARGET_CLUES

#: The patient-role account the backend seeds at startup from these two
#: settings (app/bootstrap.py). Naming them here -- before the application
#: starts -- creates the account through the application's own code rather
#: than by writing a row, and the password is generated at run time.
os.environ.setdefault("SMOKE_TEST_EMAIL", f"qa-extract-{uuid.uuid4().hex[:8]}@example.test")
os.environ.setdefault("SMOKE_TEST_PASSWORD", secrets.token_urlsafe(24))

#: What the report's caveat must say, in substance: templated note text makes
#: extraction easier here than on real clinical text.
CAVEAT_WORDS = ("template", "easier")


def _patient_findings(
    api: TestClient, admin: dict[str, str], patient_uuid: str, job: dict
) -> list[dict]:
    """Every extracted finding reachable for this patient: from the finished
    job's result and from every case read that answers 200."""
    found = list(findings(job.get("result")))
    for payload in case_payloads(api, admin, patient_uuid).values():
        found.extend(findings(payload))
    return found


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _patient_token(api: TestClient) -> str:
    email = os.environ.get("SMOKE_TEST_EMAIL")
    password = os.environ.get("SMOKE_TEST_PASSWORD")
    assert email and password, (
        "SMOKE_TEST_EMAIL and SMOKE_TEST_PASSWORD are not set, so no patient-role "
        "account exists to test the wrong-role case with."
    )
    response = api.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, (
        f"the patient-role smoke-test account cannot sign in: {response.status_code} "
        f"{response.text[:200]}"
    )
    body = response.json()
    role = str((body.get("user") or {}).get("role", "patient"))
    assert role != "admin", f"the smoke-test account is not a patient-role account: {role}"
    return str(body["token"])


# ------------------------------------------------------------------------ AC-049


def test_ac049_an_imaging_report_yields_a_finding_per_target_clue(api: TestClient) -> None:
    """AC-049: run over an imaging report describing sacroiliac findings, the
    extractor returns a structured finding for each of the pack's target clues --
    sacroiliitis wording, iliac-side-only sclerosis, erosions present or absent,
    and postpartum timing."""
    admin = admin_headers(api)
    drop = extraction_cohort(api, admin)
    uuids = patient_uuids(api, admin, drop)
    job = extraction_run(api, admin)

    found = _patient_findings(api, admin, uuids[drop.clue_patient], job)
    assert found, (
        f"the extractor returned no finding at all for the imaging report "
        f"{drop.imaging_source_ref} of patient {drop.clue_patient}, whose text is: "
        f"{drop.imaging_text!r}"
    )

    mine = [f for f in found if note_ref_of(f) == drop.imaging_source_ref] or found
    blob = " ".join(f"{clue_of(f)} {quote_of(f)}" for f in mine).lower()
    missing = [
        name for name, words in TARGET_CLUES.items() if not all(word in blob for word in words)
    ]
    assert not missing, (
        f"the extractor returned no finding for these target clues of the imaging "
        f"report {drop.imaging_source_ref}: {missing}; it returned "
        f"{[(clue_of(f), quote_of(f)) for f in mine][:10]}"
    )


def test_ac049_each_finding_quotes_its_exact_sentence_and_names_the_note(
    api: TestClient,
) -> None:
    """AC-049: each finding carries the exact sentence it came from -- a sentence
    of the note, not a paraphrase -- and the source_ref of that note."""
    admin = admin_headers(api)
    drop = extraction_cohort(api, admin)
    uuids = patient_uuids(api, admin, drop)
    job = extraction_run(api, admin)

    found = _patient_findings(api, admin, uuids[drop.clue_patient], job)
    assert found, (
        f"the extractor returned no finding for the imaging report "
        f"{drop.imaging_source_ref}, so no quoted sentence can be checked"
    )

    not_quoted = [
        (clue_of(f), quote_of(f))
        for f in found
        if quote_of(f).strip().rstrip(".") not in drop.imaging_text
    ]
    assert not not_quoted, (
        f"these findings do not quote a sentence of the note {drop.imaging_source_ref} "
        f"exactly: {not_quoted[:10]}; the note reads {drop.imaging_text!r}"
    )

    unreferenced = [clue_of(f) for f in found if note_ref_of(f) != drop.imaging_source_ref]
    assert not unreferenced, (
        f"these findings do not carry the source_ref {drop.imaging_source_ref} of the "
        f"note they came from: {unreferenced[:10]}"
    )


# ------------------------------------------------------------------------ AC-050


def test_ac050_a_clue_free_note_yields_no_finding_yet_is_recorded_as_processed(
    api: TestClient,
) -> None:
    """AC-050: a note containing none of the pack's target clues returns no finding
    rather than an invented one, and is still counted as processed."""
    admin = admin_headers(api)
    drop = extraction_cohort(api, admin)
    uuids = patient_uuids(api, admin, drop)
    job = extraction_run(api, admin)

    found = _patient_findings(api, admin, uuids[drop.clean_patient], job)
    invented = [
        (clue_of(f), quote_of(f))
        for f in found
        if note_ref_of(f) == drop.clean_source_ref or quote_of(f) in drop.clean_text
    ]
    assert not invented, (
        f"the extractor invented findings for the clue-free note "
        f"{drop.clean_source_ref} of patient {drop.clean_patient}, whose text is "
        f"{drop.clean_text!r}: {invented[:10]}"
    )

    report = extraction_report(api, admin)
    processed = report.get("notes_processed")
    assert isinstance(processed, int), (
        f"GET {EXTRACTION_REPORT} states no integer notes_processed: {str(report)[:300]}"
    )
    assert processed >= 2, (
        f"the extraction report counts {processed} notes processed, but this cohort "
        f"alone has the imaging report {drop.imaging_source_ref} and the clue-free "
        f"note {drop.clean_source_ref}; a note with no clue must still be recorded "
        "as processed"
    )


# ------------------------------------------------------------------------ AC-051


def test_ac051_an_extracted_finding_used_as_evidence_exposes_its_quote_and_note_link(
    api: TestClient,
) -> None:
    """AC-051: where an extracted finding is used as evidence in a case, the
    evidence item exposes the quoted sentence and a link back to the full note."""
    admin = admin_headers(api)
    drop = extraction_cohort(api, admin)
    uuids = patient_uuids(api, admin, drop)
    extraction_run(api, admin)
    patient_uuid = uuids[drop.clue_patient]

    payloads = case_payloads(api, admin, patient_uuid)
    assert payloads, (
        f"no case read of patient {patient_uuid} answers 200, so an evidence item "
        "resting on an extracted finding cannot be inspected"
    )

    evidence = [
        obj
        for payload in payloads.values()
        for obj in objects(payload)
        if any(key in obj for key in ("note_finding_id", "note_finding", "finding"))
        or (quote_of(obj) and obj.get("source_tag"))
    ]
    assert evidence, (
        f"no evidence item of patient {patient_uuid} rests on an extracted note "
        f"finding, so AC-051 is not being proved against anything; this patient's "
        f"imaging report {drop.imaging_source_ref} carries four target clues. "
        f"Routes read: {sorted(payloads)}"
    )

    faults: list[str] = []
    for item in evidence:
        nested = [item, *objects(item)]
        quoted = any(quote_of(obj) for obj in nested)
        linked = any(note_ref_of(obj) for obj in nested)
        if not (quoted and linked):
            faults.append(
                f"(quoted sentence: {quoted}, link to the full note: {linked}) {str(item)[:200]}"
            )
    assert not faults, (
        f"patient {patient_uuid}: these evidence items drawn from an extracted finding "
        f"do not expose both the quoted sentence and a link to the full note: "
        f"{faults[:5]}"
    )


def test_ac051_the_link_on_a_finding_resolves_to_the_full_note_text(
    api: TestClient,
) -> None:
    """AC-051: the link a finding carries is not decoration -- following it returns
    the full text of the note the quoted sentence was taken from."""
    admin = admin_headers(api)
    drop = extraction_cohort(api, admin)
    uuids = patient_uuids(api, admin, drop)
    job = extraction_run(api, admin)
    patient_uuid = uuids[drop.clue_patient]

    found = [
        f
        for f in _patient_findings(api, admin, patient_uuid, job)
        if note_ref_of(f) == drop.imaging_source_ref
    ]
    assert found, (
        f"no finding of patient {drop.clue_patient} references the imaging report "
        f"{drop.imaging_source_ref}, so no link back to the full note can be followed"
    )

    response = api.get(f"/api/cases/{patient_uuid}/notes/{drop.imaging_source_ref}", headers=admin)
    assert response.status_code == 200, (
        f"following the link of a finding -- GET /api/cases/{patient_uuid}/notes/"
        f"{drop.imaging_source_ref} -- returned {response.status_code}: "
        f"{response.text[:200]}"
    )
    text = " ".join(strings(response.json()))
    missing = [name for name, sentence in drop.clue_sentences.items() if sentence not in text]
    assert not missing, (
        f"the note the finding links to does not carry the full note text: the "
        f"sentences for {missing} are absent from {text[:300]!r}"
    )


# ------------------------------------------------------------- AC-052 / NFR-006


def test_ac052_the_extraction_report_shows_notes_processed_findings_per_clue_and_the_caveat(
    api: TestClient,
) -> None:
    """AC-052: GET /api/admin/extraction-report states the notes processed, the
    findings per clue type and the caveat that templated note text makes extraction
    easier here than on real clinical text."""
    admin = admin_headers(api)
    extraction_cohort(api, admin)
    report = extraction_report(api, admin)

    missing = [key for key in REPORT_KEYS if key not in report]
    assert not missing, (
        f"GET {EXTRACTION_REPORT} does not state {missing}; it answers {sorted(report)}"
    )

    assert isinstance(report["notes_processed"], int) and report["notes_processed"] > 0, (
        f"the report states notes_processed as {report['notes_processed']!r}"
    )

    by_clue = report["findings_by_clue"]
    assert isinstance(by_clue, dict | list) and by_clue, (
        f"the report states no findings per clue type: {by_clue!r}"
    )
    counts = (
        by_clue
        if isinstance(by_clue, dict)
        else {str(row.get("clue_type")): row.get("count") for row in by_clue}
    )
    assert all(isinstance(value, int) for value in counts.values()), (
        f"the findings per clue type are not counts: {counts}"
    )

    caveat = str(report["caveat"] or "")
    lowered = caveat.lower()
    assert all(word in lowered for word in CAVEAT_WORDS), (
        "the report's caveat does not state that the dataset's templated note text "
        f"makes extraction easier than real clinical text: {caveat!r}"
    )


def test_ac052_nfr006_the_extractor_runs_as_a_background_job_with_progress(
    api: TestClient,
) -> None:
    """AC-052 / NFR-006: the extraction run is queued as a background job that
    answers immediately, and GET /api/admin/jobs/{job_id} reports its kind,
    status and progress so no screen blocks while it runs."""
    admin = admin_headers(api)
    extraction_cohort(api, admin)

    queued = start_extraction(api, admin)
    polled = api.get(f"{JOBS}/{queued['job_id']}", headers=admin)
    assert polled.status_code == 200, (
        f"GET {JOBS}/{{job_id}} returned {polled.status_code}: {polled.text[:300]}"
    )
    body = polled.json()
    assert body.get("kind") == "extraction", (
        f"the job reports kind {body.get('kind')!r}, not 'extraction'"
    )
    assert "progress_pct" in body, (
        f"the job status carries no progress_pct, so a screen cannot show progress "
        f"while the extractor runs: {sorted(body)}"
    )

    finished = wait_for_job(api, admin, queued["job_id"])
    assert str(finished.get("status", "")).lower() in {
        "finished",
        "completed",
        "complete",
        "succeeded",
        "success",
    }, f"the extraction job did not succeed: {str(finished)[:300]}"
    progress = finished.get("progress_pct")
    assert progress is None or (0 <= float(progress) <= 100), (
        f"the finished extraction job reports progress_pct {progress!r}"
    )


# ------------------------------------------------------------- access control


def test_ac052_the_extraction_report_is_401_unauthenticated(api: TestClient) -> None:
    """Behaviour rules: no bearer token means 401 with the project's error shape."""
    response = api.get(EXTRACTION_REPORT)
    assert response.status_code == 401, (
        f"GET {EXTRACTION_REPORT} unauthenticated returned {response.status_code}: "
        f"{response.text[:200]}"
    )
    assert set(response.json()) == {"detail"}

    wrong = {"Authorization": f"Bearer {secrets.token_urlsafe(32)}"}
    revoked = api.get(EXTRACTION_REPORT, headers=wrong)
    assert revoked.status_code == 401, (
        f"GET {EXTRACTION_REPORT} with a token belonging to no session returned "
        f"{revoked.status_code}: {revoked.text[:200]}"
    )


def test_ac052_the_extraction_routes_are_403_for_a_patient_token(api: TestClient) -> None:
    """Behaviour rules: an authenticated token of the wrong role is 403."""
    headers = _bearer(_patient_token(api))

    report = api.get(EXTRACTION_REPORT, headers=headers)
    assert report.status_code == 403, (
        f"GET {EXTRACTION_REPORT} with a patient-role token returned "
        f"{report.status_code}: {report.text[:200]}"
    )
    assert set(report.json()) == {"detail"}

    started = api.post(JOBS, headers=headers, json={"kind": "extraction"})
    assert started.status_code == 403, (
        f"POST {JOBS} {{'kind': 'extraction'}} with a patient-role token returned "
        f"{started.status_code}: {started.text[:200]}"
    )


def test_ac052_no_payload_of_the_extraction_report_carries_a_credential(
    api: TestClient,
) -> None:
    """NFR-011 alongside AC-052: the report names no LLM credential value."""
    admin = admin_headers(api)
    extraction_cohort(api, admin)
    report: Any = extraction_report(api, admin)

    secret = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("LLM_API_KEY")
    if secret:
        assert all(secret not in text for text in strings(report)), (
            "the extraction report carries the LLM credential value"
        )
