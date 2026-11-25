"""US-012-5: the pack-threshold rescoring behaviour (AC-040).

Changing `thresholds.reachable_history_months` through PUT /api/admin/pack and
rescoring the cohort changes the set of patients at "Insufficient history",
with no code change, and the evaluation report states the threshold in force.

The pack is restored to its prior value in a finally block, so later suites
read the threshold they expect.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.integration.conftest import admin_headers
from tests.integration.tier_support import (
    INSUFFICIENT,
    LOWERED_THRESHOLD_MONTHS,
    PACK,
    insufficient_history_set,
    patient_token,
    read_pack,
    set_reachable_history_months,
    threshold_in_force,
    tier_cohort,
)


def _current_months(api: TestClient, admin: dict[str, str]) -> int:
    config = read_pack(api, admin)["config"]
    thresholds = config.get("thresholds") or {}
    months = thresholds.get("reachable_history_months")
    assert isinstance(months, int), (
        "the active pack declares no integer thresholds.reachable_history_months, "
        f"so AC-040 has nothing to change: {str(thresholds)[:300]}"
    )
    return months


def test_ac040_the_evaluation_report_states_the_threshold_in_force(
    api: TestClient,
) -> None:
    """[AC-040] thresholds_in_force matches the pack as stored."""
    admin = admin_headers(api)
    tier_cohort(api, admin)

    assert threshold_in_force(api, admin) == _current_months(api, admin), (
        "the evaluation report's thresholds_in_force.reachable_history_months "
        "does not match the value the active pack declares"
    )


def test_ac040_the_report_states_the_high_and_moderate_thresholds_too(
    api: TestClient,
) -> None:
    """[AC-040] The report names every threshold the contract lists."""
    admin = admin_headers(api)
    tier_cohort(api, admin)

    from tests.integration.tier_support import evaluation

    forced = evaluation(api, admin).get("thresholds_in_force")
    assert isinstance(forced, dict), (
        "GET /api/evaluation/runs/latest carries no thresholds_in_force object"
    )
    for key in ("reachable_history_months", "high", "moderate"):
        assert key in forced, f"thresholds_in_force does not state {key!r}: {str(forced)[:300]}"


def test_ac040_lowering_the_threshold_changes_the_insufficient_history_set(
    api: TestClient,
) -> None:
    """[AC-040] The set shrinks with no code change, and the report follows."""
    admin = admin_headers(api)
    drop = tier_cohort(api, admin)

    before_months = _current_months(api, admin)
    before = insufficient_history_set(api, admin)
    assert drop.mid in before, (
        f"{drop.mid} has twelve months of reachable history and the threshold "
        f"in force is {before_months} months, yet it is not at '{INSUFFICIENT}' "
        f"before the change: {sorted(before)}"
    )

    try:
        set_reachable_history_months(api, admin, LOWERED_THRESHOLD_MONTHS)

        assert threshold_in_force(api, admin) == LOWERED_THRESHOLD_MONTHS, (
            "after PUT /api/admin/pack the evaluation report still states the old "
            "reachable-history threshold, so the report does not state the "
            "threshold in force (AC-040)"
        )

        after = insufficient_history_set(api, admin)
        assert after != before, (
            "lowering thresholds.reachable_history_months from "
            f"{before_months} to {LOWERED_THRESHOLD_MONTHS} left the set of "
            f"patients at '{INSUFFICIENT}' unchanged: {sorted(after)}"
        )
        assert drop.mid not in after, (
            f"{drop.mid} has twelve months of reachable history, which clears a "
            f"{LOWERED_THRESHOLD_MONTHS}-month threshold, yet it is still at "
            f"'{INSUFFICIENT}': {sorted(after)}"
        )
        assert drop.short in after, (
            f"{drop.short} has six months of reachable history, under the "
            f"{LOWERED_THRESHOLD_MONTHS}-month threshold, yet it left "
            f"'{INSUFFICIENT}': {sorted(after)}"
        )
    finally:
        set_reachable_history_months(api, admin, before_months)

    assert threshold_in_force(api, admin) == before_months, (
        "restoring the pack did not restore the threshold the report states"
    )
    assert insufficient_history_set(api, admin) == before, (
        "restoring thresholds.reachable_history_months did not restore the set "
        "of patients at Insufficient history, so the rescoring is not a pure "
        "function of the pack value (AC-040)"
    )


def test_ac040_the_case_read_states_the_threshold_it_was_judged_against(
    api: TestClient,
) -> None:
    """[AC-040] reachable_history carries months, threshold_months, below_threshold."""
    admin = admin_headers(api)
    drop = tier_cohort(api, admin)

    from tests.integration.tier_support import case_read, uuid_of

    patient_uuid = uuid_of(api, admin, drop, drop.short)
    reachable = case_read(api, admin, patient_uuid).get("reachable_history")
    assert isinstance(reachable, dict), (
        "the case read carries no reachable_history object, which the contract requires"
    )
    for key in ("months", "threshold_months", "below_threshold"):
        assert key in reachable, f"reachable_history does not state {key!r}: {str(reachable)[:300]}"
    assert reachable["threshold_months"] == _current_months(api, admin), (
        "the case read states a reachable-history threshold other than the one "
        f"the active pack declares: {str(reachable)[:300]}"
    )
    assert reachable["below_threshold"] is True, (
        f"{drop.short} has six months of reachable history yet the case read "
        f"does not mark it below the threshold: {str(reachable)[:300]}"
    )


# ------------------------------------------------------------ access checks


def test_ac040_the_pack_route_is_401_unauthenticated(api: TestClient) -> None:
    """[AC-040] Nobody changes the threshold without signing in."""
    assert api.get(PACK).status_code == 401
    response = api.put(PACK, json={"config": {}})
    assert response.status_code == 401, (
        f"PUT {PACK} unauthenticated returned {response.status_code}, not 401"
    )


def test_ac040_the_pack_route_is_403_for_a_patient_role_token(api: TestClient) -> None:
    """[AC-040] A patient token never rescores the cohort."""
    headers = {"Authorization": f"Bearer {patient_token(api)}"}
    assert api.get(PACK, headers=headers).status_code == 403
    response = api.put(PACK, headers=headers, json={"config": {}})
    assert response.status_code == 403, (
        f"PUT {PACK} with a patient-role token returned {response.status_code}, not 403"
    )
