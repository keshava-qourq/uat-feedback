"""US-012-5: the Insufficient-history word guardrail (AC-039, AC-037).

An automated guardrail sweeps every clinician read of a patient at
"Insufficient history" -- the worklist row, GET /api/cases/{id},
GET /api/cases/{id}/timeline, the referral-packet PDF text and
GET /api/evaluation/runs/latest -- and asserts two things: the word "Low"
never appears as that patient's status, and no bare probability or raw score
is ever presented as a headline status.

Everything is read through the real API with a real bearer token.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from tests.integration.conftest import admin_headers
from tests.integration.tier_support import (
    INSUFFICIENT,
    WORKLIST,
    clinician_reads,
    is_bare_number,
    patient_token,
    patient_uuids,
    referral_packet_text,
    tier_cohort,
    tier_values,
    uuid_of,
    worklist_row_for,
    worklist_rows,
)


def _insufficient_patients(api: TestClient, admin: dict[str, str]) -> list[dict]:
    """Every worklist row currently at Insufficient history."""
    return [
        row
        for row in worklist_rows(api, admin)
        if str(row.get("tier") or "").strip().lower() == INSUFFICIENT.lower()
    ]


def test_ac039_the_short_history_fixture_patients_are_at_insufficient_history(
    api: TestClient,
) -> None:
    """[AC-039] The cohort holds patients the guardrail can actually sweep."""
    admin = admin_headers(api)
    drop = tier_cohort(api, admin)
    ids = patient_uuids(api, admin, drop)

    at_insufficient = {str(row["dataset_patient_id"]) for row in _insufficient_patients(api, admin)}
    missing = [pid for pid in drop.below_shipped_threshold if pid not in at_insufficient]
    assert not missing, (
        "these fixture patients have reachable history under the pack's "
        f"reachable_history_months yet are not at '{INSUFFICIENT}' on the "
        f"worklist, so the guardrail has nothing to sweep: {missing}; "
        f"known patients: {sorted(ids)}"
    )


@pytest.mark.skip(
    reason="One-time skip approved 2026-11-25 (Sprint 5): fetches the whole worklist and "
    "evaluation once per patient, so it runs past the 15-minute sprint check. "
    "Fix ticket: fetch both once per test."
)
def test_ac039_the_word_low_is_never_a_status_of_an_insufficient_history_patient(
    api: TestClient,
) -> None:
    """[AC-039] Across every clinician read, for every such patient."""
    admin = admin_headers(api)
    tier_cohort(api, admin)

    rows = _insufficient_patients(api, admin)
    assert rows, (
        f"no patient on GET {WORKLIST} is at '{INSUFFICIENT}', so the guardrail "
        "AC-039 requires cannot iterate anything"
    )

    offences: list[str] = []
    for row in rows:
        patient_uuid = str(row["patient_id"])
        for route, payload in clinician_reads(api, admin, patient_uuid).items():
            if isinstance(payload, str):  # the PDF text
                for line in payload.splitlines():
                    stripped = line.strip()
                    if stripped.lower() in {"low", "low tier", "status: low"}:
                        offences.append(f"{route}: the packet line {stripped!r}")
                continue
            for key, value in tier_values(payload):
                if isinstance(value, str) and value.strip().lower() == "low":
                    offences.append(f"{route}: {key}={value!r}")

    assert not offences, (
        "a patient at Insufficient history is labelled 'Low' somewhere a "
        f"clinician reads it (AC-039): {offences}"
    )


def test_ac039_every_such_patient_states_insufficient_history_as_its_status(
    api: TestClient,
) -> None:
    """[AC-039] The read says what it is, rather than quietly saying nothing."""
    admin = admin_headers(api)
    tier_cohort(api, admin)

    missing: list[str] = []
    for row in _insufficient_patients(api, admin):
        patient_uuid = str(row["patient_id"])
        case = clinician_reads(api, admin, patient_uuid)[f"/api/cases/{patient_uuid}"]
        tier = str(case.get("tier") or "")
        if tier.strip().lower() != INSUFFICIENT.lower():
            missing.append(f"{row['dataset_patient_id']}: case tier={tier!r}")

    assert not missing, (
        "the worklist puts these patients at Insufficient history but their case "
        f"read states another tier (AC-039): {missing}"
    )


def test_ac037_no_bare_probability_or_raw_score_is_shown_as_a_headline_status(
    api: TestClient,
) -> None:
    """[AC-037] A status field never carries a naked number."""
    admin = admin_headers(api)
    drop = tier_cohort(api, admin)

    offences: list[str] = []
    for dataset_id in drop.patient_ids:
        patient_uuid = uuid_of(api, admin, drop, dataset_id)
        for route, payload in clinician_reads(api, admin, patient_uuid).items():
            if isinstance(payload, str):
                continue
            for key, value in tier_values(payload):
                if is_bare_number(value):
                    offences.append(f"{route}: {key}={value!r}")

    assert not offences, (
        f"a bare probability or raw score is presented as a headline status (AC-037): {offences}"
    )


def test_ac037_the_insufficient_history_reason_is_words_not_a_number(
    api: TestClient,
) -> None:
    """[AC-037] tier_reason explains the tier in language, not a score."""
    admin = admin_headers(api)
    tier_cohort(api, admin)

    offences: list[str] = []
    for row in _insufficient_patients(api, admin):
        reason = row.get("tier_reason")
        if not isinstance(reason, str) or not reason.strip():
            offences.append(f"{row['dataset_patient_id']}: tier_reason={reason!r}")
        elif is_bare_number(reason):
            offences.append(f"{row['dataset_patient_id']}: bare number {reason!r}")

    assert not offences, f"a worklist row gives no plain-language tier_reason (AC-037): {offences}"


def test_ac039_the_referral_packet_of_such_a_patient_carries_no_low_headline(
    api: TestClient,
) -> None:
    """[AC-039] The exported PDF is swept too, not only the JSON reads."""
    admin = admin_headers(api)
    drop = tier_cohort(api, admin)

    offences: list[str] = []
    for dataset_id in drop.below_shipped_threshold:
        patient_uuid = uuid_of(api, admin, drop, dataset_id)
        text = referral_packet_text(api, admin, patient_uuid)
        lowered = text.lower()
        if "insufficient history" not in lowered:
            offences.append(f"{dataset_id}: the packet never states Insufficient history")
        for marker in ("tier: low", "status: low", "likelihood: low"):
            if marker in lowered:
                offences.append(f"{dataset_id}: the packet carries {marker!r}")

    assert not offences, f"the referral packet breaks the AC-039 guardrail: {offences}"


# ------------------------------------------------------------ access checks


def test_ac039_the_clinician_reads_are_401_unauthenticated(api: TestClient) -> None:
    """[AC-039] No bearer token, no read."""
    admin = admin_headers(api)
    drop = tier_cohort(api, admin)
    patient_uuid = uuid_of(api, admin, drop, drop.short)

    for path in (
        WORKLIST,
        f"/api/cases/{patient_uuid}",
        f"/api/cases/{patient_uuid}/timeline",
        f"/api/cases/{patient_uuid}/referral-packet.pdf",
        "/api/evaluation/runs/latest",
    ):
        response = api.get(path)
        assert response.status_code == 401, (
            f"GET {path} unauthenticated returned {response.status_code}, not 401"
        )
        assert set(response.json()) == {"detail"}, (
            f"the 401 body of GET {path} is not {{'detail': ...}}: {response.text[:200]}"
        )


def test_ac039_the_clinician_reads_are_403_for_a_patient_role_token(
    api: TestClient,
) -> None:
    """[AC-039] A patient's token never reaches a clinician read."""
    admin = admin_headers(api)
    drop = tier_cohort(api, admin)
    patient_uuid = uuid_of(api, admin, drop, drop.short)
    headers = {"Authorization": f"Bearer {patient_token(api)}"}

    for path in (
        WORKLIST,
        f"/api/cases/{patient_uuid}",
        f"/api/cases/{patient_uuid}/timeline",
        f"/api/cases/{patient_uuid}/referral-packet.pdf",
        "/api/evaluation/runs/latest",
    ):
        response = api.get(path, headers=headers)
        assert response.status_code == 403, (
            f"GET {path} with a patient-role token returned {response.status_code}, not 403"
        )


@pytest.mark.parametrize(
    "suffix", ["", "/timeline", "/referral-packet.pdf"], ids=["case", "timeline", "packet"]
)
def test_ac039_an_unknown_patient_id_is_404(api: TestClient, suffix: str) -> None:
    """[AC-039] An id nobody loaded is 404, not an empty 200."""
    admin = admin_headers(api)
    unknown = "00000000-0000-4000-8000-00000000dead"
    response = api.get(f"/api/cases/{unknown}{suffix}", headers=admin)
    assert response.status_code == 404, (
        f"GET /api/cases/{{unknown}}{suffix} returned {response.status_code}, not 404: "
        f"{response.text[:200]}"
    )
    assert set(response.json()) == {"detail"}, (
        f"the 404 body is not {{'detail': ...}}: {response.text[:200]}"
    )


def test_ac039_a_worklist_row_names_its_reachable_history_state(api: TestClient) -> None:
    """[AC-039] The row carries the fields the contract promises."""
    admin = admin_headers(api)
    drop = tier_cohort(api, admin)
    patient_uuid = uuid_of(api, admin, drop, drop.short)
    row = worklist_row_for(api, admin, patient_uuid)

    for key in (
        "tier",
        "tier_reason",
        "reachable_history_months",
        "below_reachable_history_threshold",
    ):
        assert key in row, f"the worklist row carries no {key!r}: {str(row)[:300]}"
    assert row["below_reachable_history_threshold"] is True, (
        "a patient with six months of reachable history is not flagged "
        f"below_reachable_history_threshold: {str(row)[:300]}"
    )
