"""US-012-5: the three counter-evidence scenarios, end to end (AC-033..AC-036).

Each scenario is a patient whose record the fixture drop shaped for exactly
one criterion, read through GET /api/cases/{patient_id}:

* AC-033 iliac-side-only sclerosis with erosions absent plus postpartum-timed
  onset: capped below High, each counter-evidence item listed individually,
  and the alternative explanation named.
* AC-034 widespread pain, normal CRP and poor NSAID response: capped no higher
  than Moderate, with its counter-evidence items listed.
* AC-035 load-related sacroiliac bone-marrow edema with activity-worsened
  pain: the load-related pattern recorded as counter-evidence, capped below High.
* AC-036 every fired item exposes its plain-language sentence, its triggering
  evidence with a resolvable source link, and its awaiting-sign-off marker.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.integration import fixtures_tiers as ft
from tests.integration.conftest import admin_headers
from tests.integration.tier_support import (
    case_read,
    counter_evidence_items,
    fired_words,
    item_text,
    patient_token,
    tier_cohort,
    uuid_of,
)

RANK = {"Insufficient history": 0, "Low": 1, "Moderate": 2, "High": 3}


def _rank(tier: str) -> int:
    assert tier in RANK, f"the case read states an unknown tier {tier!r}"
    return RANK[tier]


def _case_for(api: TestClient, admin: dict[str, str], role: str) -> tuple[dict, str]:
    drop = tier_cohort(api, admin)
    dataset_id = getattr(drop, role)
    patient_uuid = uuid_of(api, admin, drop, dataset_id)
    return case_read(api, admin, patient_uuid), patient_uuid


# -------------------------------------------------------------------- AC-033


def test_ac033_the_postpartum_case_is_capped_below_high(api: TestClient) -> None:
    """[AC-033] Iliac-side sclerosis, erosions absent, postpartum onset."""
    admin = admin_headers(api)
    case, _ = _case_for(api, admin, "postpartum")

    tier = str(case.get("tier") or "")
    assert _rank(tier) < RANK["High"], (
        "a case carrying iliac-side-only sclerosis with erosions absent and "
        f"postpartum-timed onset is still at {tier!r}, not capped below High "
        f"(AC-033); tier_reason: {case.get('tier_reason')!r}"
    )


def test_ac033_the_postpartum_case_lists_its_counter_evidence_items_individually(
    api: TestClient,
) -> None:
    """[AC-033] Three findings, three listed items, not one lumped sentence."""
    admin = admin_headers(api)
    case, _ = _case_for(api, admin, "postpartum")
    items = counter_evidence_items(case)

    words = fired_words(items)
    missing = [word for word in ft.AC033_WORDS if word not in words]
    assert not missing, (
        "the case read lists no counter-evidence item naming "
        f"{missing} (AC-033); it lists: {[item.get('key') for item in items]}"
    )
    assert len(items) >= len(ft.AC033_WORDS), (
        "the three findings AC-033 names must each be their own listed item; "
        f"the read lists {len(items)}: {[item.get('key') for item in items]}"
    )
    keys = [item.get("key") for item in items]
    assert len(set(keys)) == len(keys), f"counter-evidence items repeat a key: {keys}"


def test_ac033_the_postpartum_case_names_the_alternative_explanation(
    api: TestClient,
) -> None:
    """[AC-033] The read says what else explains the picture."""
    admin = admin_headers(api)
    case, _ = _case_for(api, admin, "postpartum")

    alternative = case.get("alternative_explanation")
    assert isinstance(alternative, dict), (
        "the case read carries no alternative_explanation object, so it never "
        f"names the alternative (AC-033): {str(case.get('alternative_explanation'))[:200]}"
    )
    label = alternative.get("label")
    assert isinstance(label, str) and label.strip(), (
        f"alternative_explanation carries no label: {str(alternative)[:200]}"
    )


# -------------------------------------------------------------------- AC-034


def test_ac034_the_widespread_pain_case_is_capped_no_higher_than_moderate(
    api: TestClient,
) -> None:
    """[AC-034] Widespread pain, normal CRP, poor NSAID response."""
    admin = admin_headers(api)
    case, _ = _case_for(api, admin, "widespread")

    tier = str(case.get("tier") or "")
    assert _rank(tier) <= RANK["Moderate"], (
        "a case with widespread pain, a normal CRP and poor NSAID response is "
        f"at {tier!r}, above the Moderate cap AC-034 requires; tier_reason: "
        f"{case.get('tier_reason')!r}"
    )


def test_ac034_the_widespread_pain_case_lists_its_counter_evidence_items(
    api: TestClient,
) -> None:
    """[AC-034] All three findings are listed as counter-evidence."""
    admin = admin_headers(api)
    case, _ = _case_for(api, admin, "widespread")
    items = counter_evidence_items(case)

    words = fired_words(items)
    missing = [word for word in ft.AC034_WORDS if word not in words]
    assert not missing, (
        "the case read lists no counter-evidence item naming "
        f"{missing} (AC-034); it lists: {[item.get('key') for item in items]}"
    )


def test_ac034_a_capping_item_states_the_tier_it_caps_to(api: TestClient) -> None:
    """[AC-034] effect 'cap' comes with capped_to, as the contract says."""
    admin = admin_headers(api)
    case, _ = _case_for(api, admin, "widespread")

    caps = [
        item
        for item in counter_evidence_items(case)
        if str(item.get("effect") or "").lower() == "cap"
    ]
    assert caps, (
        "no counter-evidence item of this case declares effect 'cap', so "
        f"nothing explains the Moderate cap (AC-034): {str(case.get('counter_evidence'))[:300]}"
    )
    for item in caps:
        assert item.get("capped_to") in RANK, (
            f"the capping item {item.get('key')!r} states capped_to="
            f"{item.get('capped_to')!r}, which is not a tier"
        )


# -------------------------------------------------------------------- AC-035


def test_ac035_the_load_related_case_records_the_pattern_as_counter_evidence(
    api: TestClient,
) -> None:
    """[AC-035] Load-related bone-marrow edema with activity-worsened pain."""
    admin = admin_headers(api)
    case, _ = _case_for(api, admin, "load")
    items = counter_evidence_items(case)

    words = fired_words(items)
    missing = [word for word in ft.AC035_WORDS if word not in words]
    assert not missing, (
        "the case read records no counter-evidence item naming the load-related "
        f"pattern {missing} (AC-035); it lists: {[item.get('key') for item in items]}"
    )


def test_ac035_the_load_related_case_is_capped_below_high(api: TestClient) -> None:
    """[AC-035] The load-related pattern caps the tier."""
    admin = admin_headers(api)
    case, _ = _case_for(api, admin, "load")

    tier = str(case.get("tier") or "")
    assert _rank(tier) < RANK["High"], (
        "a case with load-related sacroiliac bone-marrow edema and "
        f"activity-worsened pain is still at {tier!r}, not capped below High "
        f"(AC-035); tier_reason: {case.get('tier_reason')!r}"
    )


# -------------------------------------------------------------------- AC-036


def test_ac036_every_fired_item_exposes_a_plain_language_sentence(
    api: TestClient,
) -> None:
    """[AC-036] Plain language, not a key."""
    admin = admin_headers(api)
    offences: list[str] = []
    for role in ("postpartum", "widespread", "load"):
        case, _ = _case_for(api, admin, role)
        for item in counter_evidence_items(case):
            sentence = item.get("plain_language")
            if not isinstance(sentence, str) or len(sentence.split()) < 3:
                offences.append(f"{role}/{item.get('key')!r}: plain_language={sentence!r}")

    assert not offences, (
        f"a fired counter-evidence item has no plain-language sentence (AC-036): {offences}"
    )


def test_ac036_every_fired_item_lists_its_triggering_evidence(api: TestClient) -> None:
    """[AC-036] Each item names what fired it, with a date and a source tag."""
    admin = admin_headers(api)
    offences: list[str] = []
    for role in ("postpartum", "widespread", "load"):
        case, _ = _case_for(api, admin, role)
        for item in counter_evidence_items(case):
            evidence = item.get("evidence")
            if not isinstance(evidence, list) or not evidence:
                offences.append(f"{role}/{item.get('key')!r}: evidence={evidence!r}")
                continue
            for entry in evidence:
                if not isinstance(entry, dict):
                    offences.append(f"{role}/{item.get('key')!r}: evidence entry {entry!r}")
                    continue
                for key in ("display", "date", "source_tag", "source_ref"):
                    if not str(entry.get(key) or "").strip():
                        offences.append(f"{role}/{item.get('key')!r}: evidence has no {key}")

    assert not offences, (
        f"a fired counter-evidence item does not expose its triggering evidence (AC-036): "
        f"{offences[:12]}"
    )


def test_ac036_the_source_link_of_each_triggering_evidence_item_resolves(
    api: TestClient,
) -> None:
    """[AC-036] The source_ref is resolvable, not a dangling string."""
    admin = admin_headers(api)
    offences: list[str] = []
    for role in ("postpartum", "widespread", "load"):
        case, patient_uuid = _case_for(api, admin, role)
        timeline = api.get(f"/api/cases/{patient_uuid}/timeline", headers=admin)
        assert timeline.status_code == 200, (
            f"GET /api/cases/{patient_uuid}/timeline returned {timeline.status_code}"
        )
        known = {
            str(item.get("source_ref"))
            for item in (timeline.json().get("items") or [])
            if isinstance(item, dict) and item.get("source_ref")
        }
        for row in (timeline.json().get("items") or []):
            for source in (row.get("sources") or []) if isinstance(row, dict) else []:
                if isinstance(source, dict) and source.get("source_ref"):
                    known.add(str(source["source_ref"]))

        for item in counter_evidence_items(case):
            for entry in item.get("evidence") or []:
                if not isinstance(entry, dict):
                    continue
                ref = str(entry.get("source_ref") or "")
                if not ref:
                    continue
                note = api.get(f"/api/cases/{patient_uuid}/notes/{ref}", headers=admin)
                if note.status_code != 200 and ref not in known:
                    offences.append(
                        f"{role}/{item.get('key')!r}: source_ref {ref!r} resolves to "
                        f"neither a note ({note.status_code}) nor a timeline item"
                    )

    assert not offences, f"a counter-evidence source link does not resolve (AC-036): {offences}"


def test_ac036_every_fired_item_carries_its_awaiting_sign_off_marker(
    api: TestClient,
) -> None:
    """[AC-036] The marker is present and boolean wherever it applies."""
    admin = admin_headers(api)
    offences: list[str] = []
    for role in ("postpartum", "widespread", "load"):
        case, _ = _case_for(api, admin, role)
        for item in counter_evidence_items(case):
            if "awaiting_sign_off" not in item:
                offences.append(f"{role}/{item.get('key')!r}: no awaiting_sign_off field")
            elif not isinstance(item["awaiting_sign_off"], bool):
                offences.append(
                    f"{role}/{item.get('key')!r}: awaiting_sign_off="
                    f"{item['awaiting_sign_off']!r} is not a boolean"
                )

    assert not offences, (
        f"a fired counter-evidence item carries no awaiting-sign-off marker (AC-036): {offences}"
    )


def test_ac036_no_counter_evidence_item_is_shown_as_a_bare_key(api: TestClient) -> None:
    """[AC-036] Each item carries a human label alongside its key."""
    admin = admin_headers(api)
    offences: list[str] = []
    for role in ("postpartum", "widespread", "load"):
        case, _ = _case_for(api, admin, role)
        for item in counter_evidence_items(case):
            label = item.get("label")
            if not isinstance(label, str) or not label.strip():
                offences.append(f"{role}/{item.get('key')!r}: label={label!r}")
            elif label.strip() == str(item.get("key") or "").strip():
                offences.append(f"{role}: the label is the raw key {label!r}")
            assert item_text(item), "a counter-evidence item carries no text at all"

    assert not offences, f"a counter-evidence item shows a bare key (AC-036): {offences}"


# ------------------------------------------------------------ access checks


def test_ac033_the_case_read_is_401_unauthenticated(api: TestClient) -> None:
    """[AC-033] The scenario reads need a bearer token."""
    admin = admin_headers(api)
    drop = tier_cohort(api, admin)
    patient_uuid = uuid_of(api, admin, drop, drop.postpartum)

    response = api.get(f"/api/cases/{patient_uuid}")
    assert response.status_code == 401, (
        f"GET /api/cases/{patient_uuid} unauthenticated returned {response.status_code}"
    )


def test_ac034_the_case_read_is_403_for_a_patient_role_token(api: TestClient) -> None:
    """[AC-034] A patient token never reads another patient's case."""
    admin = admin_headers(api)
    drop = tier_cohort(api, admin)
    patient_uuid = uuid_of(api, admin, drop, drop.widespread)
    headers = {"Authorization": f"Bearer {patient_token(api)}"}

    response = api.get(f"/api/cases/{patient_uuid}", headers=headers)
    assert response.status_code == 403, (
        f"GET /api/cases/{patient_uuid} with a patient token returned "
        f"{response.status_code}, not 403"
    )


def test_ac035_an_unknown_patient_id_is_404(api: TestClient) -> None:
    """[AC-035] An unknown id never answers a counter-evidence payload."""
    admin = admin_headers(api)
    unknown = "00000000-0000-4000-8000-0000000c0ffe"
    response = api.get(f"/api/cases/{unknown}", headers=admin)
    assert response.status_code == 404, (
        f"GET /api/cases/{{unknown}} returned {response.status_code}, not 404"
    )
    assert set(response.json()) == {"detail"}, (
        f"the 404 body is not {{'detail': ...}}: {response.text[:200]}"
    )
