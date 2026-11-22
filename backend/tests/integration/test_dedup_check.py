"""US-004-4: de-duplication of EHR and claim views of the same encounter, proved
against the running API (AC-011, AC-012, AC-013).

Everything goes through the real HTTP API against the sandbox's PostgreSQL and
Redis: the bootstrap admin signs in through POST /api/auth/login (the only
sign-in), the cohort is loaded once for this module through
POST /api/admin/ingest-runs over a fixture drop whose encounter truth the test
knows, and the de-duplication check is run exactly as the contract says a
screen runs it -- POST /api/admin/jobs {"kind": "dedup_check"} and then
GET /api/admin/jobs/{job_id}. No row is written by hand.

Every assertion message names the patient and the encounter involved, so a
failure here is a defect report rather than a puzzle.
"""

from __future__ import annotations

import os
import secrets
import uuid

from fastapi.testclient import TestClient

from tests.integration.conftest import admin_headers
from tests.integration.dedup_support import (
    JOBS,
    dedup_cohort,
    dedup_report,
    objects,
    patient_uuids,
    source_tags,
    start_dedup_check,
    strings,
    timeline_items,
)
from tests.integration.fixtures_dedup import EXPECTED_REPORT, REPORT_KEYS

#: The patient-role account the backend seeds at startup from these two
#: settings (app/bootstrap.py). Naming them here -- before the application
#: starts -- creates the account through the application's own code rather
#: than by writing a row, and the password is generated at run time.
os.environ.setdefault("SMOKE_TEST_EMAIL", f"qa-dedup-patient-{uuid.uuid4().hex[:8]}@example.test")
os.environ.setdefault("SMOKE_TEST_PASSWORD", secrets.token_urlsafe(24))

#: Where a visit-count signal may arrive in a payload.
VISIT_COUNT_KEYS = (
    "visit_count",
    "visits",
    "visit_counts",
    "encounter_count",
    "occurrences",
    "occurrence_count",
)


def _entries_for(items: list[dict], *, encounter_ref: str, when: str) -> list[dict]:
    """The timeline entries that represent the encounter at `when`.

    An entry belongs to the encounter when it carries its `encounter_ref`, or
    failing that when it is dated on the same instant: a merged entry may keep
    the ref or may carry a merged encounter id of its own.
    """
    by_ref = [item for item in items if str(item.get("encounter_ref") or "") == encounter_ref]
    if by_ref:
        return by_ref
    day = when[:10]
    return [
        item
        for item in items
        if str(item.get("item_time") or item.get("event_time") or "")[:10] == day
    ]


# ------------------------------------------------------------------------ AC-011


def test_ac011_an_encounter_in_both_sources_is_one_entry_tagged_with_both(
    api: TestClient,
) -> None:
    """AC-011: an encounter recorded by an EHR source and by a claim source
    produces exactly one timeline entry, tagged with both contributing sources."""
    admin = admin_headers(api)
    drop = dedup_cohort(api, admin)
    uuids = patient_uuids(api, admin, drop)
    patient = uuids[drop.merged_patient]

    items = timeline_items(api, admin, patient)
    entries = _entries_for(items, encounter_ref=drop.merged_encounter_ref, when=drop.merged_time)

    assert len(entries) == 1, (
        f"patient {drop.merged_patient} ({patient}), encounter "
        f"{drop.merged_encounter_ref} at {drop.merged_time}: the EHR row and the claim "
        f"row describing it produced {len(entries)} timeline entries, not one merged "
        f"entry: {str(entries)[:400]}"
    )

    tags = source_tags(entries[0])
    assert {"ehr", "claim"} <= tags, (
        f"patient {drop.merged_patient} ({patient}), encounter "
        f"{drop.merged_encounter_ref}: the merged entry is tagged {sorted(tags)}, so it "
        "does not name both contributing sources (ehr and claim): "
        f"{str(entries[0])[:400]}"
    )


def test_ac011_the_merged_encounter_is_counted_once_in_a_visit_count_signal(
    api: TestClient,
) -> None:
    """AC-011: the visit the two source rows describe is counted once, not twice."""
    admin = admin_headers(api)
    drop = dedup_cohort(api, admin)
    uuids = patient_uuids(api, admin, drop)
    patient = uuids[drop.merged_patient]

    response = api.get(f"/api/cases/{patient}/timeline", headers=admin)
    assert response.status_code == 200, (
        f"GET /api/cases/{patient}/timeline returned {response.status_code}: "
        f"{response.text[:300]}"
    )
    payload = response.json()
    items = payload.get("items") or []

    encounters = [
        item
        for item in items
        if str(item.get("event_type") or "") == "encounter"
        and str(item.get("item_time") or item.get("event_time") or "")[:10] == drop.merged_date
    ]
    assert len(encounters) == 1, (
        f"patient {drop.merged_patient} ({patient}): the visit on {drop.merged_date} "
        f"(encounter {drop.merged_encounter_ref}) counts {len(encounters)} times in the "
        f"encounters of the unified timeline: {str(encounters)[:400]}"
    )

    counted = [
        (key, obj[key])
        for obj in objects(payload)
        for key in VISIT_COUNT_KEYS
        if isinstance(obj.get(key), int)
    ]
    wrong = [(key, value) for key, value in counted if value != 1]
    assert not wrong, (
        f"patient {drop.merged_patient} ({patient}) has exactly one real visit "
        f"({drop.merged_encounter_ref} on {drop.merged_date}), but a visit-count signal "
        f"reports: {wrong}"
    )


# ------------------------------------------------------------------------ AC-012


def test_ac012_the_check_runs_as_a_job_and_reports_matched_split_and_merged_in_error(
    api: TestClient,
) -> None:
    """AC-012: the de-duplication check runs through POST /api/admin/jobs and its
    report, read from GET /api/admin/jobs/{job_id}, states how many true
    encounters matched one merged entry, how many were split into more than one
    entry and how many source rows were merged in error, against
    encounter_truth.csv."""
    admin = admin_headers(api)
    drop = dedup_cohort(api, admin)
    patient_uuids(api, admin, drop)

    result = dedup_report(api, admin)

    missing = [key for key in REPORT_KEYS if key not in result]
    assert not missing, (
        f"the de-duplication report for dataset {drop.dataset_version} states nothing "
        f"for: {missing}; it carries {sorted(result)}"
    )

    wrong = {
        key: (result.get(key), expected)
        for key, expected in EXPECTED_REPORT.items()
        if result.get(key) != expected
    }
    assert not wrong, (
        "the de-duplication report does not match encounter_truth.csv for dataset "
        f"{drop.dataset_version} (patients {drop.merged_patient} with the doubly-sourced "
        f"encounter {drop.merged_encounter_ref}, {drop.single_patient} with "
        f"{drop.single_encounter_ref}, and the invisible encounter "
        f"{drop.invisible_encounter_id}) -- key: (reported, expected): {wrong}"
    )


def test_ac012_the_report_names_the_dataset_version_it_checked(api: TestClient) -> None:
    """AC-012: the report is attributable -- it states which loaded dataset the
    numbers belong to."""
    admin = admin_headers(api)
    drop = dedup_cohort(api, admin)
    patient_uuids(api, admin, drop)

    result = dedup_report(api, admin)
    assert result.get("dataset_version") == drop.dataset_version, (
        f"the de-duplication report states dataset_version "
        f"{result.get('dataset_version')!r}; the cohort it checked was loaded as "
        f"{drop.dataset_version!r}"
    )


def test_ac012_the_job_reports_its_kind_and_progress_while_it_runs(api: TestClient) -> None:
    """AC-012 / the contract: GET /api/admin/jobs/{job_id} answers
    {job_id, kind, status, progress_pct, result} for the queued check."""
    admin = admin_headers(api)
    drop = dedup_cohort(api, admin)
    patient_uuids(api, admin, drop)

    queued = start_dedup_check(api, admin)
    response = api.get(f"{JOBS}/{queued['job_id']}", headers=admin)
    assert response.status_code == 200, (
        f"GET {JOBS}/{{job_id}} returned {response.status_code}: {response.text[:300]}"
    )
    body = response.json()
    for key in ("job_id", "kind", "status", "progress_pct", "result"):
        assert key in body, f"the job status carries no {key!r}: {str(body)[:300]}"
    assert body["job_id"] == queued["job_id"]
    assert body["kind"] == "dedup_check", (
        f"the job reports kind {body['kind']!r}, not 'dedup_check'"
    )


# ------------------------------------------------------------------------ AC-013


def test_ac013_an_encounter_in_no_source_is_counted_as_invisible_care(
    api: TestClient,
) -> None:
    """AC-013: a true encounter present in encounter_truth.csv but in no EHR or
    claim source is counted as invisible care."""
    admin = admin_headers(api)
    drop = dedup_cohort(api, admin)
    patient_uuids(api, admin, drop)

    result = dedup_report(api, admin)
    assert result.get("invisible_care") == EXPECTED_REPORT["invisible_care"], (
        f"patient {drop.merged_patient}, true encounter {drop.invisible_encounter_id} at "
        f"{drop.invisible_time} is in encounter_truth.csv and in no source, so exactly "
        f"{EXPECTED_REPORT['invisible_care']} encounter is invisible care; the report "
        f"states {result.get('invisible_care')!r}"
    )


def test_ac013_invisible_care_is_never_drawn_in_a_timeline_case_view_or_export(
    api: TestClient,
) -> None:
    """AC-013: the invisible encounter appears in no timeline, no case view and no
    export -- the product may only show what its sources contain."""
    admin = admin_headers(api)
    drop = dedup_cohort(api, admin)
    uuids = patient_uuids(api, admin, drop)
    patient = uuids[drop.merged_patient]
    markers = (drop.invisible_encounter_id, drop.invisible_date, drop.invisible_time)

    drawn: list[str] = []
    for path in (
        f"/api/cases/{patient}/timeline",
        f"/api/cases/{patient}",
        f"/api/cases/{patient}/evidence",
    ):
        response = api.get(path, headers=admin)
        if response.status_code != 200:
            continue
        text = " ".join(strings(response.json()))
        for marker in markers:
            if marker in text:
                drawn.append(f"{path} shows {marker!r}")

    export = api.get(f"/api/cases/{patient}/referral-packet.pdf", headers=admin)
    if export.status_code == 200:
        body = export.content.decode("latin-1", "replace")
        for marker in markers:
            if marker in body:
                drawn.append(f"the referral packet export shows {marker!r}")

    assert not drawn, (
        f"patient {drop.merged_patient} ({patient}): the invisible encounter "
        f"{drop.invisible_encounter_id} at {drop.invisible_time} is in no EHR or claim "
        f"source, so nothing may draw it, but: {drawn}"
    )


# --------------------------------------------------------------- access control


def _patient_token(api: TestClient) -> str:
    """A patient-role session token, obtained through the one sign-in route."""
    email = os.environ.get("SMOKE_TEST_EMAIL")
    password = os.environ.get("SMOKE_TEST_PASSWORD")
    assert email and password, (
        "SMOKE_TEST_EMAIL and SMOKE_TEST_PASSWORD are not set, so no patient-role "
        "account exists to test the wrong-role case with."
    )
    response = api.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, (
        f"the patient-role account cannot sign in: {response.status_code} "
        f"{response.text[:200]}"
    )
    body = response.json()
    role = str((body.get("user") or {}).get("role", "patient"))
    assert role != "admin", f"the smoke-test account is not a non-admin account: {role}"
    return str(body["token"])


def test_ac012_the_job_routes_are_401_unauthenticated(api: TestClient) -> None:
    """Behaviour rules: no bearer token means 401 on both job routes, with the
    project's one error shape."""
    queued = api.post(JOBS, json={"kind": "dedup_check"})
    assert queued.status_code == 401, (
        f"POST {JOBS} unauthenticated returned {queued.status_code}: {queued.text[:200]}"
    )
    assert set(queued.json()) == {"detail"}

    read = api.get(f"{JOBS}/{uuid.uuid4()}")
    assert read.status_code == 401, (
        f"GET {JOBS}/{{job_id}} unauthenticated returned {read.status_code}: {read.text[:200]}"
    )
    assert set(read.json()) == {"detail"}

    wrong = {"Authorization": f"Bearer {secrets.token_urlsafe(32)}"}
    refused = api.post(JOBS, headers=wrong, json={"kind": "dedup_check"})
    assert refused.status_code == 401, (
        f"POST {JOBS} with a token that belongs to no session returned "
        f"{refused.status_code}: {refused.text[:200]}"
    )


def test_ac012_the_job_routes_are_403_for_a_patient_token(api: TestClient) -> None:
    """Behaviour rules: an authenticated token of the wrong role is 403, never 200."""
    headers = {"Authorization": f"Bearer {_patient_token(api)}"}

    queued = api.post(JOBS, headers=headers, json={"kind": "dedup_check"})
    assert queued.status_code == 403, (
        f"POST {JOBS} with a patient token returned {queued.status_code}: {queued.text[:200]}"
    )
    assert set(queued.json()) == {"detail"}

    read = api.get(f"{JOBS}/{uuid.uuid4()}", headers=headers)
    assert read.status_code == 403, (
        f"GET {JOBS}/{{job_id}} with a patient token returned {read.status_code}: "
        f"{read.text[:200]}"
    )
    assert set(read.json()) == {"detail"}


def test_ac012_an_unknown_job_id_is_404(api: TestClient) -> None:
    """Behaviour rules: a job id that belongs to no job is not found."""
    admin = admin_headers(api)
    response = api.get(f"{JOBS}/{uuid.uuid4()}", headers=admin)

    assert response.status_code == 404, (
        f"GET {JOBS}/{{unknown job id}} returned {response.status_code}: {response.text[:200]}"
    )
    assert set(response.json()) == {"detail"}


def test_ac012_an_unknown_job_kind_is_422(api: TestClient) -> None:
    """Behaviour rules: a value outside the enumerated `kind` set is 422."""
    admin = admin_headers(api)
    response = api.post(JOBS, headers=admin, json={"kind": f"not-a-kind-{uuid.uuid4().hex[:6]}"})

    assert response.status_code == 422, (
        f"POST {JOBS} with an unknown kind returned {response.status_code}: "
        f"{response.text[:200]}"
    )
    assert set(response.json()) == {"detail"}
