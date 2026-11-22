"""US-003-4: the leakage guarantee, proved end to end against the running API and
the loaded cohort (AC-008, AC-009, AC-010, AC-028, AC-029, NFR-013).

Everything goes through the real HTTP API against the sandbox's PostgreSQL and
Redis: the bootstrap admin signs in through POST /api/auth/login (the only
sign-in), the cohort is loaded once for this module through
POST /api/admin/ingest-runs over a leakage fixture drop whose ground truth the
test knows, and every assertion reads what an API route answers. No row is
written by hand.

Every assertion message names the patient and the offending field or item date,
so a failure here is a defect report rather than a puzzle.
"""

from __future__ import annotations

import importlib
from datetime import date
from typing import Any

import pytest
from fastapi.testclient import TestClient

from tests.integration.conftest import admin_headers
from tests.integration.fixtures_leakage import (
    GROUND_TRUTH_COLUMNS,
    OPERATIONAL_COLUMNS,
    LeakageDrop,
)
from tests.integration.leakage_support import (
    cutoff_of,
    leakage_cohort,
    patient_uuids,
    post_cutoff_items,
    rendered_reads,
    strings,
    worklist_rows,
)

EVALUATION = "/api/evaluation/runs/latest"

#: Words that name a ground-truth label column, in any spelling a payload may use.
GROUND_TRUTH_KEY_WORDS = (
    "archetype",
    "typicality",
    "clue_density",
    "cluedensity",
    "hla_b27_true",
    "hlab27",
    "axspa_label",
    "axspalabel",
    "ground_truth",
    "simulated_diagnosis_date",
)


def _cohort(api: TestClient, admin: dict[str, str]) -> LeakageDrop:
    return leakage_cohort(api, admin)


def _ground_truth_hits(payload: Any, drop: LeakageDrop, dataset_id: str) -> list[str]:
    """Every ground-truth value or column name a payload carries, named."""
    found = set(strings(payload))
    hits: list[str] = []
    for column, value in drop.ground_truth[dataset_id].items():
        if value and value in found:
            hits.append(f"the value of {column} ({value!r})")
    lowered = {text.lower() for text in found}
    for word in GROUND_TRUTH_KEY_WORDS:
        if word in lowered:
            hits.append(f"the field name {word!r}")
    return hits


# ------------------------------------------------------------- AC-029 / NFR-013


def test_ac029_nfr013_no_rendered_read_of_any_patient_carries_a_post_cutoff_item(
    api: TestClient,
) -> None:
    """AC-029 / NFR-013: across every patient of the loaded cohort, every rendered
    read contains zero items dated on or after that patient's evaluation cutoff;
    an undated family-history row is the only exception."""
    admin = admin_headers(api)
    drop = _cohort(api, admin)
    known = {
        uuid: drop.cutoffs[dataset_id]
        for dataset_id, uuid in patient_uuids(api, admin, drop).items()
    }

    violations: list[str] = []
    uncheckable: list[str] = []
    checked = 0
    for row in worklist_rows(api, admin):
        patient_uuid = str(row["patient_id"])
        dataset_id = str(row["dataset_patient_id"])
        payloads = rendered_reads(api, admin, patient_uuid)
        if not payloads:
            continue
        cutoff: date | None = known.get(patient_uuid)
        for payload in payloads.values():
            cutoff = cutoff or cutoff_of(payload)
        if cutoff is None:
            uncheckable.append(dataset_id)
            continue
        checked += 1
        for route, payload in payloads.items():
            for key, when, label in post_cutoff_items(payload, cutoff):
                violations.append(
                    f"patient {dataset_id} ({patient_uuid}) on {route}: {key}={when} "
                    f"is on or after the cutoff {cutoff.isoformat()} -- {label}"
                )

    assert not uncheckable, (
        "these patients' rendered reads state no evaluation cutoff, so the "
        f"leakage guarantee cannot be checked for them: {sorted(uncheckable)[:20]}"
    )
    assert checked, "no patient of the loaded cohort could be read, so nothing was checked"
    assert not violations, (
        f"{len(violations)} post-cutoff items are rendered; AC-029 requires zero: "
        f"{violations[:20]}"
    )


def test_ac029_nfr013_the_undated_family_history_row_is_the_one_allowed_exception(
    api: TestClient,
) -> None:
    """AC-029 / NFR-013: the check above is not vacuous -- the pre-cutoff history and
    the undated family-history row are still rendered, so items are being shown."""
    admin = admin_headers(api)
    drop = _cohort(api, admin)
    case_uuid = patient_uuids(api, admin, drop)[drop.case_id]
    payloads = rendered_reads(api, admin, case_uuid)
    assert payloads, (
        f"patient {drop.case_id} ({case_uuid}) has no readable case view, so the "
        "leakage guarantee is proved against nothing"
    )
    shown = {text for payload in payloads.values() for text in strings(payload)}

    assert drop.pre_cutoff_display in shown, (
        f"patient {drop.case_id}: the pre-cutoff item {drop.pre_cutoff_display!r} is not "
        "rendered, so the case view shows no history at all"
    )
    assert drop.undated_family_history_display in shown, (
        f"patient {drop.case_id}: the undated family-history row "
        f"{drop.undated_family_history_display!r} is not rendered; NFR-013 makes it the "
        "one exception to the post-cutoff filter"
    )


def test_ac029_an_item_dated_exactly_on_the_cutoff_is_excluded(api: TestClient) -> None:
    """AC-029: the cutoff is inclusive -- an item dated on the cutoff day itself is
    not rendered."""
    admin = admin_headers(api)
    drop = _cohort(api, admin)
    case_uuid = patient_uuids(api, admin, drop)[drop.case_id]
    payloads = rendered_reads(api, admin, case_uuid)
    assert payloads, f"patient {drop.case_id} ({case_uuid}) has no readable case view"

    leaked = [
        route
        for route, payload in payloads.items()
        if drop.on_cutoff_display in set(strings(payload))
    ]
    assert not leaked, (
        f"patient {drop.case_id}: the item dated {drop.cutoff.isoformat()}, exactly on the "
        f"evaluation cutoff, is rendered on {leaked}; the boundary is inclusive"
    )


# ------------------------------------------------------------- AC-008 / NFR-013


def test_ac008_nfr013_no_ground_truth_field_reaches_any_rendered_patient_payload(
    api: TestClient,
) -> None:
    """AC-008: archetype, typicality, clue_density, hla_b27_true and the axSpA label
    appear in no scoring input, no feature and no rendered patient payload."""
    admin = admin_headers(api)
    drop = _cohort(api, admin)
    uuids = patient_uuids(api, admin, drop)

    leaks: list[str] = []
    for dataset_id, patient_uuid in uuids.items():
        payloads = dict(rendered_reads(api, admin, patient_uuid))
        for path in (
            f"/api/cases/{patient_uuid}/score",
            f"/api/cases/{patient_uuid}/features",
            f"/api/demo/personas/{drop.persona_key}/replay",
        ):
            response = api.get(path, headers=admin)
            if response.status_code == 200:
                payloads[path] = response.json()
        opened = api.post(
            f"/api/demo/personas/{drop.persona_key}/open",
            headers=admin,
            json={"view": "clinician"},
        )
        if opened.status_code == 200:
            payloads[f"POST /api/demo/personas/{drop.persona_key}/open"] = opened.json()

        for route, payload in payloads.items():
            for hit in _ground_truth_hits(payload, drop, dataset_id):
                leaks.append(f"patient {dataset_id} ({patient_uuid}) on {route}: {hit}")

    assert not leaks, (
        f"ground truth reaches {len(leaks)} rendered payloads; AC-008 requires none: "
        f"{leaks[:20]}"
    )


def test_ac008_the_patients_own_screens_carry_no_ground_truth(api: TestClient) -> None:
    """AC-008: the patient-facing reads carry no label field either."""
    admin = admin_headers(api)
    drop = _cohort(api, admin)

    leaks: list[str] = []
    for path in (
        "/api/worklist",
        "/api/patients/me/timeline",
        "/api/patients/me/updates",
        "/api/patients/me/visit-prep",
        "/api/demo/personas",
    ):
        response = api.get(path, headers=admin)
        if response.status_code != 200:
            continue
        payload = response.json()
        for dataset_id in drop.patient_ids:
            for hit in _ground_truth_hits(payload, drop, dataset_id):
                leaks.append(f"patient {dataset_id} on {path}: {hit}")
    assert not leaks, f"these reads carry a ground-truth field: {leaks[:20]}"


# ------------------------------------------------------------------------ AC-028


def test_ac028_a_confirmed_case_shows_neither_its_diagnosis_nor_its_workup(
    api: TestClient,
) -> None:
    """AC-028: for a confirmed case whose cutoff is 30 days before its diagnosis,
    the case evidence, the criteria and the timeline show neither the diagnosis
    nor the rheumatology workup that followed it."""
    admin = admin_headers(api)
    drop = _cohort(api, admin)
    case_uuid = patient_uuids(api, admin, drop)[drop.case_id]
    assert (drop.diagnosis_date - drop.cutoff).days == 30, (
        "the fixture's cutoff is not 30 days before the diagnosis, so AC-028 is not "
        "being tested as written"
    )

    payloads = rendered_reads(api, admin, case_uuid)
    assert payloads, (
        f"patient {drop.case_id} ({case_uuid}) has no readable evidence, criteria or "
        "timeline, so AC-028 cannot be proved"
    )

    leaks: list[str] = []
    for route, payload in payloads.items():
        shown = set(strings(payload))
        if drop.diagnosis_display in shown:
            leaks.append(
                f"patient {drop.case_id} on {route}: the diagnosis "
                f"{drop.diagnosis_display!r} dated {drop.diagnosis_date.isoformat()} "
                f"(cutoff {drop.cutoff.isoformat()})"
            )
        for workup in drop.workup_displays:
            if workup in shown:
                leaks.append(
                    f"patient {drop.case_id} on {route}: the rheumatology workup item "
                    f"{workup!r}, dated after the cutoff {drop.cutoff.isoformat()}"
                )
    assert not leaks, f"the confirmed diagnosis or its workup is visible: {leaks}"


# ------------------------------------------------------------------------ AC-010


def test_ac010_only_the_cutoff_and_the_split_reach_the_engine_or_the_demo_path(
    api: TestClient,
) -> None:
    """AC-010: of the labels store, only eval_cutoff_date and split reach the engine
    or the demo path; no ground-truth column does."""
    admin = admin_headers(api)
    drop = _cohort(api, admin)
    uuids = patient_uuids(api, admin, drop)

    payloads: dict[str, Any] = {}
    for dataset_id, patient_uuid in uuids.items():
        for route, payload in rendered_reads(api, admin, patient_uuid).items():
            payloads[f"{route} [{dataset_id}]"] = payload
        for path in (f"/api/cases/{patient_uuid}/score", f"/api/cases/{patient_uuid}/features"):
            response = api.get(path, headers=admin)
            if response.status_code == 200:
                payloads[f"{path} [{dataset_id}]"] = response.json()
    replay = api.get(f"/api/demo/personas/{drop.persona_key}/replay", headers=admin)
    if replay.status_code == 200:
        payloads[f"/api/demo/personas/{drop.persona_key}/replay"] = replay.json()

    assert payloads, (
        "no engine or demo route answered for the leakage cohort, so what the labels "
        "store hands them cannot be inspected"
    )

    leaks: list[str] = []
    for route, payload in payloads.items():
        lowered = {text.lower() for text in strings(payload)}
        for column in GROUND_TRUTH_COLUMNS:
            if column in lowered:
                leaks.append(f"{route}: the labels column {column!r}")
    assert not leaks, (
        f"these ground-truth label columns reach the engine or the demo path: {leaks[:20]}; "
        f"only {OPERATIONAL_COLUMNS} may"
    )


def test_ac010_the_operational_accessor_refuses_a_ground_truth_field(api: TestClient) -> None:
    """AC-010: asking the labels store's operational accessor for a ground-truth
    field is refused, rather than quietly answering with it."""
    try:
        labels = importlib.import_module("app.labels")
    except ModuleNotFoundError as exc:  # the module this ticket builds
        pytest.fail(
            "the labels store (backend/app/labels.py) does not exist, so AC-010's "
            f"operational accessor cannot refuse anything: {exc}"
        )

    accessor = next(
        (
            getattr(labels, name)
            for name in ("operational_field", "operational", "get_operational", "field_for_engine")
            if callable(getattr(labels, name, None))
        ),
        None,
    )
    assert accessor is not None, (
        "app.labels exposes no operational accessor (one of operational_field, "
        f"operational, get_operational, field_for_engine): it has {sorted(dir(labels))[:40]}"
    )

    for column in OPERATIONAL_COLUMNS:
        try:
            accessor(column)
        except LookupError:
            pass  # no row loaded in this process is acceptable; being refused is not
        except Exception as exc:  # noqa: BLE001 - the message is the defect report
            pytest.fail(
                f"the operational accessor refused {column!r}, which AC-010 allows: "
                f"{type(exc).__name__}: {exc}"
            )

    allowed: list[str] = []
    for column in GROUND_TRUTH_COLUMNS:
        try:
            accessor(column)
        except LookupError:
            allowed.append(column)
        except Exception:  # noqa: BLE001 - refusal is what the criterion requires
            continue
        else:
            allowed.append(column)
    assert not allowed, (
        "the operational accessor answered for these ground-truth fields instead of "
        f"refusing them: {allowed}"
    )


# ------------------------------------------------------------------------ AC-009


def test_ac009_the_evaluation_report_still_reports_sensitivity_and_ppv(
    api: TestClient,
) -> None:
    """AC-009: the evaluation report is the one component that may read ground
    truth, so it still reports sensitivity and PPV."""
    admin = admin_headers(api)
    _cohort(api, admin)

    response = api.get(EVALUATION, headers=admin)
    assert response.status_code == 200, (
        f"GET {EVALUATION} returned {response.status_code}: {response.text[:300]}"
    )
    payload = response.json()
    lowered = " ".join(strings(payload)).lower()

    missing = [
        name
        for name, words in (
            ("sensitivity", ("sensitivity", "recall")),
            ("PPV", ("ppv", "positive predictive value", "precision")),
        )
        if not any(word in lowered for word in words)
    ]
    assert not missing, (
        f"the evaluation report names no {missing}; AC-009 requires the evaluation "
        f"report -- the one component that may read ground truth -- to report both: "
        f"{response.text[:300]}"
    )
