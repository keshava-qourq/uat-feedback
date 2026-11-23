"""US-010-3: the criteria panel of GET /api/cases/{patient_id} (AC-030, AC-031,
AC-032), proved against the real API and the cohort the environment already
serves.

Everything goes through the real HTTP API against the sandbox's PostgreSQL:
the bootstrap admin signs in through POST /api/auth/login, the patient ids come
from GET /api/worklist, and an ingest is started only when the environment has
no cohort at all (NFR-021 serialises ingest, so a 409 is tolerated). No row is
written by hand and no application module is imported to read data.

The expected criteria are not written down here: they are read from the active
condition pack through GET /api/admin/pack, so this file stays true as the pack
changes (AC-021 / NFR-019).
"""

from __future__ import annotations

import os
import secrets
import uuid
from typing import Any

import pytest
from fastapi.testclient import TestClient

from tests.integration.conftest import admin_headers
from tests.integration.invite_support import bearer, ingest_cohort, objects, strings

PACK = "/api/admin/pack"
WORKLIST = "/api/worklist"

#: The non-admin account the wrong-role check signs in as: the backend seeds a
#: patient-role user from these two at startup, so naming them here -- before
#: the application starts -- creates the account through the application's own
#: code rather than by writing a row.
os.environ.setdefault("SMOKE_TEST_EMAIL", f"qa-patient-{uuid.uuid4().hex[:8]}@example.test")
os.environ.setdefault("SMOKE_TEST_PASSWORD", secrets.token_urlsafe(24))

#: The three statuses AC-030 allows, in any spelling the payload may use.
ALLOWED_STATUSES = {"met", "not_met", "notmet", "not met", "unknown"}

#: Where a criterion item's status may arrive.
STATUS_KEYS = ("status", "state", "result")

#: Where a criterion item's key may arrive.
KEY_KEYS = ("criterion_key", "key", "item_key", "criterion")

#: Where the supporting evidence of a met item may arrive.
EVIDENCE_KEYS = (
    "supporting_evidence",
    "evidence",
    "supporting_item",
    "support",
    "source",
    "answer",
)

#: Where an item's date may arrive.
DATE_KEYS = ("item_date", "date", "event_time", "answered_at", "note_time", "occurred_at")

#: Where an item's source tag may arrive.
SOURCE_KEYS = ("source_tag", "source_type", "source", "sources", "source_tags")

#: Where "what would answer it" may arrive on an unknown item.
NEEDED_KEYS = (
    "what_would_answer_it",
    "what_is_needed",
    "what_we_still_need",
    "needed",
    "missing",
    "how_to_answer",
)

#: Where the SPARTAN point total may arrive.
TOTAL_KEYS = ("total", "points_total", "score", "spartan_total", "points")

#: Where the pack's referral threshold may arrive beside the total.
THRESHOLD_KEYS = ("threshold", "pass_score", "referral_threshold", "pass_threshold")


# --------------------------------------------------------------------- helpers


def pack_criteria(api: TestClient, admin: dict[str, str]) -> dict[str, Any]:
    """The active pack's criteria section, read through the admin pack route."""
    response = api.get(PACK, headers=admin)
    assert response.status_code == 200, (
        f"GET {PACK} returned {response.status_code}, so the criteria the panel must "
        f"list are unknown: {response.text[:300]}"
    )
    config = response.json().get("config")
    assert isinstance(config, dict) and config, (
        f"GET {PACK} answers no pack configuration: {response.text[:300]}"
    )
    criteria = config.get("criteria")
    assert isinstance(criteria, dict) and criteria, (
        f"the active pack carries no criteria section: {sorted(config)}"
    )
    return criteria


def spartan_block(criteria: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """The pack's SPARTAN points criterion: `(its key, its definition)`."""
    for key, value in criteria.items():
        if not isinstance(value, dict):
            continue
        text = f"{key} {value.get('label', '')}".lower()
        if "spartan" in text or value.get("kind") == "points":
            return key, value
    raise AssertionError(f"the active pack declares no SPARTAN point criterion: {sorted(criteria)}")


def asas_keys(criteria: dict[str, Any]) -> list[str]:
    """Every ASAS criterion key the pack declares."""
    found = [
        key
        for key, value in criteria.items()
        if isinstance(value, dict)
        and "asas" in f"{key} {value.get('label', '')}".lower()
    ]
    assert found, f"the active pack declares no ASAS criterion: {sorted(criteria)}"
    return found


def case_payload(api: TestClient, admin: dict[str, str]) -> tuple[str, dict]:
    """A patient of the loaded cohort and their case read: `(uuid, payload)`."""
    cohort = ingest_cohort(api, admin)
    failures: list[str] = []
    for dataset_id, patient_uuid in sorted(cohort.items()):
        response = api.get(f"/api/cases/{patient_uuid}", headers=admin)
        if response.status_code == 200:
            return patient_uuid, response.json()
        failures.append(f"{dataset_id} ({patient_uuid}): {response.status_code}")
    raise AssertionError(
        "no patient of the loaded cohort answers GET /api/cases/{patient_id} with 200, "
        f"so the criteria panel cannot be read at all: {failures[:10]}"
    )


def any_patient_uuid(api: TestClient, admin: dict[str, str]) -> str:
    """One patient uuid of the loaded cohort, whatever its case read answers."""
    cohort = ingest_cohort(api, admin)
    return sorted(cohort.values())[0]


def criteria_items(payload: Any) -> list[dict]:
    """Every criterion row of a case payload, however the panel is nested."""
    return [
        obj
        for obj in objects(payload)
        if any(key in obj for key in KEY_KEYS) and any(key in obj for key in STATUS_KEYS)
    ]


def item_key(item: dict) -> str:
    for key in KEY_KEYS:
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def item_status(item: dict) -> str:
    for key in STATUS_KEYS:
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip().lower()
    return ""


def panel_keys(items: list[dict]) -> set[str]:
    return {item_key(item).lower() for item in items}


def spartan_total_block(payload: Any) -> dict:
    """The object carrying the SPARTAN total, searched at any depth."""
    candidates = [
        obj
        for obj in objects(payload)
        if any(key in obj for key in TOTAL_KEYS)
        and "spartan" in " ".join(strings(obj)).lower() + " " + " ".join(obj.keys()).lower()
    ]
    if not candidates:
        candidates = [
            obj
            for obj in objects(payload)
            if any(key in obj for key in TOTAL_KEYS)
            and any(key in obj for key in THRESHOLD_KEYS)
        ]
    assert candidates, (
        "the case read states no SPARTAN point total; AC-030 requires the total to be "
        f"shown against the pack's referral threshold: {str(payload)[:400]}"
    )
    return candidates[0]


def number(block: dict, keys: tuple[str, ...]) -> float | None:
    for key in keys:
        value = block.get(key)
        if isinstance(value, bool):
            continue
        if isinstance(value, int | float):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                continue
    return None


def patient_token(api: TestClient) -> str:
    """A patient-role session token, obtained through the one sign-in route."""
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


# ------------------------------------------------------------------------ AC-030


def test_ac030_every_asas_criterion_and_spartan_point_item_is_listed_with_a_status(
    api: TestClient,
) -> None:
    """AC-030: a staff read of GET /api/cases/{patient_id} lists every ASAS criterion
    and every SPARTAN point item the active pack declares, each with a status of
    met, not met or unknown."""
    admin = admin_headers(api)
    criteria = pack_criteria(api, admin)
    spartan_key, spartan = spartan_block(criteria)
    expected = {key.lower() for key in asas_keys(criteria)}
    expected |= {str(key).lower() for key in (spartan.get("items") or {})}
    assert expected, "the pack declares neither an ASAS criterion nor a SPARTAN point item"

    patient_uuid, payload = case_payload(api, admin)
    items = criteria_items(payload)
    assert items, (
        f"the case read for patient {patient_uuid} carries no criteria panel; AC-030 "
        f"requires every ASAS criterion and SPARTAN point item to be listed: "
        f"{str(payload)[:400]}"
    )

    shown = panel_keys(items)
    missing = sorted(key for key in expected if key not in shown)
    assert not missing, (
        f"patient {patient_uuid}: the criteria panel does not list these criteria the "
        f"pack declares ({spartan_key} items included): {missing}; it lists {sorted(shown)}"
    )

    bad = [
        f"{item_key(item)!r}={item_status(item)!r}"
        for item in items
        if item_status(item) not in ALLOWED_STATUSES
    ]
    assert not bad, (
        f"patient {patient_uuid}: these criteria carry a status that is not met, "
        f"not_met or unknown: {bad[:20]}"
    )


def test_ac030_the_spartan_total_is_shown_against_the_packs_referral_threshold(
    api: TestClient,
) -> None:
    """AC-030: the SPARTAN total is shown beside the referral threshold the active
    pack configures, with the same value the pack carries."""
    admin = admin_headers(api)
    criteria = pack_criteria(api, admin)
    _key, spartan = spartan_block(criteria)
    pack_threshold = spartan.get("pass_score")
    assert isinstance(pack_threshold, int | float), (
        f"the pack's SPARTAN criterion carries no numeric pass_score: {spartan}"
    )

    patient_uuid, payload = case_payload(api, admin)
    block = spartan_total_block(payload)

    total = number(block, TOTAL_KEYS)
    assert total is not None, (
        f"patient {patient_uuid}: the SPARTAN block states no numeric total: {block}"
    )
    threshold = number(block, THRESHOLD_KEYS)
    assert threshold is not None, (
        f"patient {patient_uuid}: the SPARTAN total is not shown against a referral "
        f"threshold: {block}"
    )
    assert threshold == float(pack_threshold), (
        f"patient {patient_uuid}: the case read shows the threshold as {threshold}, but "
        f"the active pack configures {pack_threshold}"
    )


# ------------------------------------------------------------------------ AC-031


def test_ac031_a_met_criterion_names_its_event_or_intake_answer_with_date_and_source_tag(
    api: TestClient,
) -> None:
    """AC-031: every criterion marked met names the underlying event or intake
    answer it rests on, with that item's date and its source tag."""
    admin = admin_headers(api)
    pack_criteria(api, admin)
    patient_uuid, payload = case_payload(api, admin)
    items = criteria_items(payload)
    assert items, f"patient {patient_uuid}: the case read carries no criteria panel"

    met = [item for item in items if item_status(item) == "met"]
    assert met, (
        f"patient {patient_uuid}: no criterion of the panel is met, so AC-031 is not "
        "being proved against anything; the cohort must contain a patient who meets at "
        "least one criterion"
    )

    faults: list[str] = []
    for item in met:
        nested: list[dict] = [item]
        for key in EVIDENCE_KEYS:
            nested.extend(objects(item.get(key)))
        names_item = any(
            isinstance(obj.get(name), str) and str(obj.get(name)).strip()
            for obj in nested
            for name in ("event_id", "note_finding_id", "question_key", "label", "display", "text")
        )
        dated = any(obj.get(name) for obj in nested for name in DATE_KEYS)
        tagged = any(obj.get(name) for obj in nested for name in SOURCE_KEYS)
        if not (names_item and dated and tagged):
            faults.append(
                f"{item_key(item)!r} (names the item: {names_item}, has a date: {dated}, "
                f"has a source tag: {tagged}): {str(item)[:200]}"
            )
    assert not faults, (
        f"patient {patient_uuid}: these met criteria do not name their underlying event "
        f"or intake answer with a date and a source tag: {faults[:10]}"
    )


# ------------------------------------------------------------------------ AC-032


def test_ac032_an_unknown_criterion_states_what_would_answer_it(api: TestClient) -> None:
    """AC-032: every criterion marked unknown from available data states what would
    be needed to answer it."""
    admin = admin_headers(api)
    pack_criteria(api, admin)
    patient_uuid, payload = case_payload(api, admin)
    items = criteria_items(payload)
    assert items, f"patient {patient_uuid}: the case read carries no criteria panel"

    unknown = [item for item in items if item_status(item) == "unknown"]
    assert unknown, (
        f"patient {patient_uuid}: no criterion of the panel is unknown, so AC-032 is "
        "not being proved; a cohort patient must have at least one criterion that "
        "cannot be answered from available data"
    )

    silent = [
        item_key(item)
        for item in unknown
        if not any(
            isinstance(item.get(key), str) and item.get(key, "").strip()
            for key in NEEDED_KEYS
        )
    ]
    assert not silent, (
        f"patient {patient_uuid}: these unknown criteria state nothing about what would "
        f"answer them: {silent}; the panel items read {str(unknown[:2])[:300]}"
    )


def test_ac032_the_spartan_total_counts_met_points_only(api: TestClient) -> None:
    """AC-032: an unknown item is never silently counted as not met -- the SPARTAN
    total equals the sum of the pack's points for the met items only."""
    admin = admin_headers(api)
    criteria = pack_criteria(api, admin)
    _key, spartan = spartan_block(criteria)
    points = {str(k).lower(): float(v) for k, v in (spartan.get("items") or {}).items()}
    assert points, f"the pack's SPARTAN criterion declares no point items: {spartan}"

    patient_uuid, payload = case_payload(api, admin)
    items = criteria_items(payload)
    met_points = sum(
        points[item_key(item).lower()]
        for item in items
        if item_key(item).lower() in points and item_status(item) == "met"
    )

    block = spartan_total_block(payload)
    total = number(block, TOTAL_KEYS)
    assert total is not None, (
        f"patient {patient_uuid}: the SPARTAN block states no numeric total: {block}"
    )
    assert total == met_points, (
        f"patient {patient_uuid}: the SPARTAN total is {total}, but the met point items "
        f"sum to {met_points}; unknown items must not be counted. Panel: "
        f"{[(item_key(i), item_status(i)) for i in items][:20]}"
    )


# ------------------------------------------------------------- access control


def test_ac030_the_case_read_is_401_unauthenticated(api: TestClient) -> None:
    """Behaviour rules: no bearer token means 401 with the project's error shape."""
    admin = admin_headers(api)
    patient_uuid = any_patient_uuid(api, admin)

    response = api.get(f"/api/cases/{patient_uuid}")
    assert response.status_code == 401, (
        f"GET /api/cases/{patient_uuid} unauthenticated returned {response.status_code}: "
        f"{response.text[:200]}"
    )
    assert set(response.json()) == {"detail"}

    wrong = {"Authorization": f"Bearer {secrets.token_urlsafe(32)}"}
    revoked = api.get(f"/api/cases/{patient_uuid}", headers=wrong)
    assert revoked.status_code == 401, (
        f"GET /api/cases/{patient_uuid} with a token that belongs to no session returned "
        f"{revoked.status_code}: {revoked.text[:200]}"
    )


def test_ac030_the_case_read_is_403_for_a_patient_role_token(api: TestClient) -> None:
    """Behaviour rules: an authenticated token of the wrong role is 403, never 200."""
    admin = admin_headers(api)
    patient_uuid = any_patient_uuid(api, admin)

    response = api.get(f"/api/cases/{patient_uuid}", headers=bearer(patient_token(api)))
    assert response.status_code == 403, (
        f"GET /api/cases/{patient_uuid} with a patient-role token returned "
        f"{response.status_code}: {response.text[:200]}"
    )
    assert set(response.json()) == {"detail"}


def test_ac030_an_unknown_patient_id_is_404(api: TestClient) -> None:
    """Behaviour rules: an unknown patient id is not found."""
    admin = admin_headers(api)
    response = api.get(f"/api/cases/{uuid.uuid4()}", headers=admin)

    assert response.status_code == 404, (
        f"an unknown patient id returned {response.status_code}: {response.text[:200]}"
    )
    assert set(response.json()) == {"detail"}


@pytest.mark.parametrize("suffix", ["", "/criteria"])
def test_ac030_the_criteria_panel_is_part_of_the_case_read(api: TestClient, suffix: str) -> None:
    """AC-030: the criteria panel is reachable on the contract's route -- the case
    read itself; a separate /criteria route, if offered, answers the same panel."""
    admin = admin_headers(api)
    patient_uuid, payload = case_payload(api, admin)

    if suffix:
        response = api.get(f"/api/cases/{patient_uuid}{suffix}", headers=admin)
        if response.status_code == 404:
            return  # the contract puts the panel on the case read itself
        assert response.status_code == 200, (
            f"GET /api/cases/{patient_uuid}{suffix} returned {response.status_code}: "
            f"{response.text[:200]}"
        )
        payload = response.json()

    assert criteria_items(payload), (
        f"GET /api/cases/{patient_uuid}{suffix} carries no criteria panel: "
        f"{str(payload)[:300]}"
    )
