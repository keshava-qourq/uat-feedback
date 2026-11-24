"""Shared helpers for the tier-guarantee acceptance tests (US-012-5).

The cohort is built the way the behaviour rules and NFR-021 require: the
patients come from whatever GET /api/worklist already serves, and a tier
fixture drop is ingested once per module only when this environment has no
cohort that can exercise the criteria. A 409 (ingest is serialised one run at
a time) is tolerated. Nothing is written into the database by hand.

Every read goes through the real API with a bearer token obtained from
POST /api/auth/login.
"""

from __future__ import annotations

import io
import os
import re
import uuid
from typing import Any

from fastapi.testclient import TestClient

from tests.integration import fixtures_dataset as fx
from tests.integration import fixtures_tiers as ft
from tests.integration.conftest import wait_for_run
from tests.integration.fixtures_tiers import TierDrop

INGEST_START = "/api/admin/ingest-runs"
WORKLIST = "/api/worklist"
PACK = "/api/admin/pack"
EVALUATION = "/api/evaluation/runs/latest"

INSUFFICIENT = "Insufficient history"

#: Where a tier may arrive in a payload.
TIER_KEYS = ("tier", "status", "tier_label", "headline_tier")

#: A bare probability or raw score shown as a headline status (AC-037).
BARE_NUMBER = re.compile(r"^\s*-?\d+(?:\.\d+)?\s*%?\s*$")

#: The word a patient at Insufficient history must never be labelled with.
FORBIDDEN_TIER_WORD = "Low"


# --------------------------------------------------------------------- walking


def objects(payload: Any) -> list[dict]:
    found: list[dict] = []
    if isinstance(payload, dict):
        found.append(payload)
        for value in payload.values():
            found.extend(objects(value))
    elif isinstance(payload, list):
        for item in payload:
            found.extend(objects(item))
    return found


def strings(payload: Any) -> list[str]:
    if isinstance(payload, str):
        return [payload]
    if isinstance(payload, dict):
        out: list[str] = []
        for key, value in payload.items():
            out.append(str(key))
            out.extend(strings(value))
        return out
    if isinstance(payload, list):
        out = []
        for item in payload:
            out.extend(strings(item))
        return out
    return [] if payload is None else [str(payload)]


def tier_values(payload: Any) -> list[tuple[str, Any]]:
    """Every (key, value) in `payload` that states a status/tier."""
    found: list[tuple[str, Any]] = []
    for obj in objects(payload):
        for key in TIER_KEYS:
            if key in obj:
                found.append((key, obj[key]))
    return found


def is_bare_number(value: Any) -> bool:
    """True when a value is a bare probability or raw score with no words."""
    if isinstance(value, bool):
        return False
    if isinstance(value, int | float):
        return True
    return isinstance(value, str) and bool(BARE_NUMBER.match(value))


# ------------------------------------------------------------------ the cohort


def drain_ingest_queue() -> None:
    """Run whatever is on the queues, as the deployed RQ worker would."""
    import redis
    from rq import Queue, SimpleWorker

    connection = redis.from_url(os.environ["REDIS_URL"])
    queues = [Queue(name, connection=connection) for name in ("ingest", "default")]
    SimpleWorker(queues, connection=connection).work(burst=True)


def worklist_rows(api: TestClient, admin: dict[str, str]) -> list[dict]:
    response = api.get(WORKLIST, headers=admin)
    assert response.status_code == 200, (
        f"GET {WORKLIST} returned {response.status_code}: {response.text[:200]}"
    )
    return [
        row
        for row in objects(response.json())
        if row.get("patient_id") and row.get("dataset_patient_id")
    ]


_STATE: dict[str, Any] = {}


def _ingest_tier_drop(api: TestClient, admin: dict[str, str]) -> TierDrop:
    drop = TierDrop(uuid.uuid4().hex[:8])
    source_uri, _prefix = fx.upload_fixture_set(drop.files())
    for attempt in range(2):
        drain_ingest_queue()
        response = api.post(
            INGEST_START,
            headers=admin,
            json={
                "dataset_version": drop.dataset_version,
                "source_uri": source_uri,
                "seed": 41,
            },
        )
        drain_ingest_queue()
        if response.status_code == 409 and attempt == 0:
            continue
        assert response.status_code in (200, 202), (
            f"starting the tier cohort's ingest run returned {response.status_code}: "
            f"{response.text[:300]}"
        )
        wait_for_run(api, admin, response.json()["run_id"])
        drain_ingest_queue()
        break
    return drop


def tier_cohort(api: TestClient, admin: dict[str, str]) -> TierDrop:
    """The tier fixture cohort, loaded once per module through the real API."""
    existing = _STATE.get("drop")
    if isinstance(existing, TierDrop):
        return existing
    wanted = None
    rows = worklist_rows(api, admin)
    # Only ingest when this environment carries no tier fixture cohort at all.
    for row in rows:
        if str(row.get("dataset_patient_id", "")).startswith("TIERSHORT-"):
            wanted = row
            break
    if wanted is None:
        drop = _ingest_tier_drop(api, admin)
    else:
        drop = TierDrop(str(wanted["dataset_patient_id"]).split("-", 1)[1])
    _STATE["drop"] = drop
    return drop


def patient_uuids(api: TestClient, admin: dict[str, str], drop: TierDrop) -> dict[str, str]:
    """dataset patient id -> internal uuid for this drop, from the worklist."""
    wanted = set(drop.patient_ids)
    found = {
        str(row["dataset_patient_id"]): str(row["patient_id"])
        for row in worklist_rows(api, admin)
        if row.get("dataset_patient_id") in wanted
    }
    assert set(found) == wanted, (
        "these tier fixture patients are not visible through GET "
        f"{WORKLIST}, so the tier guarantees cannot be checked over them: "
        f"{sorted(wanted - set(found))}"
    )
    return found


def uuid_of(api: TestClient, admin: dict[str, str], drop: TierDrop, dataset_id: str) -> str:
    return patient_uuids(api, admin, drop)[dataset_id]


# --------------------------------------------------------------- the reads


def worklist_row_for(api: TestClient, admin: dict[str, str], patient_uuid: str) -> dict:
    for row in worklist_rows(api, admin):
        if str(row["patient_id"]) == patient_uuid:
            return row
    raise AssertionError(f"patient {patient_uuid} has no row on GET {WORKLIST}")


def case_read(api: TestClient, admin: dict[str, str], patient_uuid: str) -> dict:
    response = api.get(f"/api/cases/{patient_uuid}", headers=admin)
    assert response.status_code == 200, (
        f"GET /api/cases/{patient_uuid} returned {response.status_code}: {response.text[:300]}"
    )
    return response.json()


def case_timeline(api: TestClient, admin: dict[str, str], patient_uuid: str) -> dict:
    response = api.get(f"/api/cases/{patient_uuid}/timeline", headers=admin)
    assert response.status_code == 200, (
        f"GET /api/cases/{patient_uuid}/timeline returned {response.status_code}: "
        f"{response.text[:300]}"
    )
    return response.json()


def evaluation(api: TestClient, admin: dict[str, str]) -> dict:
    response = api.get(EVALUATION, headers=admin)
    assert response.status_code == 200, (
        f"GET {EVALUATION} returned {response.status_code}: {response.text[:300]}"
    )
    return response.json()


def pdf_text(data: bytes) -> str:
    import pypdf

    reader = pypdf.PdfReader(io.BytesIO(data))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def referral_packet_text(api: TestClient, admin: dict[str, str], patient_uuid: str) -> str:
    response = api.get(f"/api/cases/{patient_uuid}/referral-packet.pdf", headers=admin)
    assert response.status_code == 200, (
        f"GET /api/cases/{patient_uuid}/referral-packet.pdf returned "
        f"{response.status_code}: {response.text[:200]}"
    )
    return pdf_text(response.content)


def clinician_reads(api: TestClient, admin: dict[str, str], patient_uuid: str) -> dict[str, Any]:
    """Every clinician read of one patient AC-039 names, route -> payload."""
    return {
        WORKLIST: worklist_row_for(api, admin, patient_uuid),
        f"/api/cases/{patient_uuid}": case_read(api, admin, patient_uuid),
        f"/api/cases/{patient_uuid}/timeline": case_timeline(api, admin, patient_uuid),
        f"/api/cases/{patient_uuid}/referral-packet.pdf": referral_packet_text(
            api, admin, patient_uuid
        ),
        EVALUATION: evaluation(api, admin),
    }


# ----------------------------------------------------------- counter-evidence


def counter_evidence_items(case: dict) -> list[dict]:
    """The case read's counter_evidence list, exactly as the contract names it."""
    items = case.get("counter_evidence")
    assert isinstance(items, list), (
        "the case read carries no counter_evidence list, which the contract "
        f"requires: {str(case)[:300]}"
    )
    return [item for item in items if isinstance(item, dict)]


def item_text(item: dict) -> str:
    """The words one counter-evidence item shows a clinician."""
    return " ".join(
        str(item.get(key) or "") for key in ("key", "label", "plain_language")
    ).lower()


def fired_words(items: list[dict]) -> str:
    return " ".join(item_text(item) for item in items)


# --------------------------------------------------------------------- tokens


def patient_token(api: TestClient) -> str:
    """A patient-role session token, through the one sign-in route."""
    email = os.environ.get("SMOKE_TEST_EMAIL")
    password = os.environ.get("SMOKE_TEST_PASSWORD")
    assert email and password, (
        "SMOKE_TEST_EMAIL and SMOKE_TEST_PASSWORD are not set: the platform sets them "
        "for every run and the backend creates that account at startup."
    )
    response = api.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, (
        f"the patient-role account cannot sign in: {response.status_code} {response.text[:200]}"
    )
    return str(response.json()["token"])


# ----------------------------------------------------------------- the pack


def read_pack(api: TestClient, admin: dict[str, str]) -> dict:
    response = api.get(PACK, headers=admin)
    assert response.status_code == 200, (
        f"GET {PACK} returned {response.status_code}: {response.text[:300]}"
    )
    body = response.json()
    config = body.get("config")
    assert isinstance(config, dict), (
        f"GET {PACK} carries no pack configuration to change: {str(body)[:300]}"
    )
    return body


def write_pack(api: TestClient, admin: dict[str, str], config: dict, summary: str) -> dict:
    response = api.put(
        PACK, headers=admin, json={"config": config, "change_summary": summary}
    )
    assert response.status_code in (200, 201), (
        f"PUT {PACK} returned {response.status_code}: {response.text[:300]}"
    )
    return response.json()


def set_reachable_history_months(
    api: TestClient, admin: dict[str, str], months: int
) -> None:
    """Change thresholds.reachable_history_months through PUT /api/admin/pack."""
    body = read_pack(api, admin)
    config = dict(body["config"])
    thresholds = dict(config.get("thresholds") or {})
    thresholds["reachable_history_months"] = months
    config["thresholds"] = thresholds
    write_pack(api, admin, config, f"QA US-012-5: reachable_history_months -> {months}")


def insufficient_history_set(api: TestClient, admin: dict[str, str]) -> set[str]:
    """The dataset patient ids the worklist currently puts at Insufficient history."""
    return {
        str(row["dataset_patient_id"])
        for row in worklist_rows(api, admin)
        if str(row.get("tier") or "").strip().lower() == INSUFFICIENT.lower()
    }


def threshold_in_force(api: TestClient, admin: dict[str, str]) -> Any:
    """What the evaluation report states the reachable-history threshold is."""
    report = evaluation(api, admin)
    forced = report.get("thresholds_in_force")
    assert isinstance(forced, dict), (
        "the evaluation report carries no thresholds_in_force object, so it does "
        f"not state the threshold in force (AC-040): {str(report)[:300]}"
    )
    assert "reachable_history_months" in forced, (
        "thresholds_in_force does not state reachable_history_months: "
        f"{str(forced)[:300]}"
    )
    return forced["reachable_history_months"]


SHIPPED_THRESHOLD_MONTHS = ft.SHIPPED_THRESHOLD_MONTHS
LOWERED_THRESHOLD_MONTHS = ft.LOWERED_THRESHOLD_MONTHS
