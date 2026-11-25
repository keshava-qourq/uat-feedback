"""The condition pack: loading, validation, the generic accessors, and the
no-pack-active start (AC-020, AC-022, NFR-019)."""

from __future__ import annotations

import copy

import pytest
import yaml

from app.pack import registry


@pytest.fixture(autouse=True)
def _clean_registry():
    registry.reload()
    yield
    registry.reload()


@pytest.fixture
def pack_key() -> str:
    keys = registry.list_packs()
    assert keys, "at least one pack file must ship"
    return keys[0]


@pytest.fixture
def raw(pack_key: str) -> dict:
    path = registry.PACKS_DIR / f"{pack_key}.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


# --------------------------------------------------------------- AC-020 content


def test_ac020_the_shipped_pack_declares_every_required_section(pack_key: str) -> None:
    pack = registry.load_pack(pack_key)

    for section in (
        "code_lists",
        "signals",
        "criteria",
        "counter_evidence",
        "thresholds",
        "workup_items",
        "copy",
    ):
        assert pack.section(section), f"{section} is empty"


def test_ac020_every_code_list_names_its_system_and_carries_codes(pack_key: str) -> None:
    for key, entry in registry.load_pack(pack_key).code_lists().items():
        assert entry["system"], key
        assert entry["codes"], key


def test_ac020_criteria_cover_both_a_set_rule_and_a_points_rule(pack_key: str) -> None:
    kinds = {rule["kind"] for rule in registry.load_pack(pack_key).criteria().values()}

    assert {"set", "points"} <= kinds


def test_ac020_every_counter_evidence_rule_declares_its_demotion_effect(pack_key: str) -> None:
    """Each rule names an effect the pack's `demotion_rules` section declares,
    and the tier field that effect reads (US-012-2 adds the capping effect
    alongside the demoting one, so neither name is spelled out here)."""
    pack = registry.load_pack(pack_key)
    effects = pack.section("demotion_rules") or {}

    assert effects, "the pack declares no demotion rules"
    for key, rule in pack.counter_evidence().items():
        effect = effects.get(rule["effect"])
        assert isinstance(effect, dict), key
        assert rule.get(effect["tier_from"]), key


def test_ac020_every_workup_item_carries_its_reasoning_text(pack_key: str) -> None:
    for key, item in registry.load_pack(pack_key).workup_items().items():
        assert item["reasoning"].strip(), key


def test_ac020_the_pack_carries_patient_facing_copy_strings(pack_key: str) -> None:
    copy_strings = registry.load_pack(pack_key).copy()

    assert copy_strings
    assert all(isinstance(value, str) and value.strip() for value in copy_strings.values())


# ------------------------------------------------------------------- validation


def test_ac020_a_missing_section_is_reported_naming_the_offending_key(raw: dict) -> None:
    broken = copy.deepcopy(raw)
    del broken["thresholds"]

    with pytest.raises(registry.PackValidationError) as exc:
        registry.validate(broken)

    assert exc.value.key == "thresholds"


def test_ac020_a_malformed_item_is_reported_naming_the_offending_key(raw: dict) -> None:
    broken = copy.deepcopy(raw)
    first = next(iter(broken["workup_items"]))
    del broken["workup_items"][first]["reasoning"]

    with pytest.raises(registry.PackValidationError) as exc:
        registry.validate(broken)

    assert exc.value.key == f"workup_items.{first}.reasoning"


def test_ac020_a_threshold_that_is_not_a_number_names_its_key(raw: dict) -> None:
    broken = copy.deepcopy(raw)
    first = next(iter(broken["thresholds"]))
    broken["thresholds"][first] = "high-ish"

    with pytest.raises(registry.PackValidationError) as exc:
        registry.validate(broken)

    assert exc.value.key == f"thresholds.{first}"


def test_ac020_loading_an_unknown_pack_key_names_that_key() -> None:
    with pytest.raises(registry.PackValidationError) as exc:
        registry.load_pack("no-such-pack")

    assert exc.value.key == "no-such-pack"


# -------------------------------------------------------------- generic accessors


def test_ac020_every_accessor_answers_by_key(pack_key: str) -> None:
    pack = registry.load_pack(pack_key)
    pairs = (
        (pack.code_lists, pack.code_list),
        (pack.signals, pack.signal),
        (pack.criteria, pack.criterion),
        (pack.counter_evidence, pack.counter_evidence_rule),
        (pack.thresholds, pack.threshold),
        (pack.workup_items, pack.workup_item),
    )
    for listing, by_key in pairs:
        items = listing()
        first = next(iter(items))
        assert by_key(first) == items[first]
        assert by_key("not-there") is None

    assert pack.copy_text(next(iter(pack.copy())))
    assert pack.copy_text("not-there", "fallback") == "fallback"
    assert isinstance(pack.prohibited_terms(), list)
    assert pack.section("not-there") is None


def test_ac020_listing_packs_includes_the_shipped_pack(pack_key: str) -> None:
    assert pack_key in registry.list_packs()


# ---------------------------------------------------------- AC-022 disabled pack


def test_ac022_no_pack_is_active_when_the_pack_is_disabled(monkeypatch, pack_key: str) -> None:
    monkeypatch.setenv("CONDITION_PACK_ENABLED", "false")
    monkeypatch.setenv("CONDITION_PACK_KEY", pack_key)

    assert registry.get_active_pack() is None
    assert registry.active_pack_status() == {"active": False, "key": None}


def test_ac022_no_pack_is_active_when_the_key_is_blank(monkeypatch) -> None:
    monkeypatch.delenv("CONDITION_PACK_ENABLED", raising=False)
    monkeypatch.setenv("CONDITION_PACK_KEY", "   ")

    assert registry.get_active_pack() is None
    assert registry.active_pack_status()["active"] is False


def test_ac022_the_configured_pack_is_active_when_enabled(monkeypatch, pack_key: str) -> None:
    monkeypatch.setenv("CONDITION_PACK_ENABLED", "true")
    monkeypatch.setenv("CONDITION_PACK_KEY", pack_key)

    pack = registry.get_active_pack()

    assert pack is not None
    assert registry.active_pack_status() == {"active": True, "key": pack_key}


def test_ac022_health_reports_that_no_condition_pack_is_active(client, monkeypatch) -> None:
    """The app stays up with no pack; `/health` keeps its contracted shape.

    `GET /health` is fixed by the API spec as {status, db, cache, queue}, so
    which pack is active is reported by `app.pack.active_pack_status` (and the
    admin settings route that serves it), not in the health body.
    """
    monkeypatch.delenv("CONDITION_PACK_KEY", raising=False)

    body = client.get("/health").json()

    assert body["status"] == "ok"
    assert set(body) == {"status", "db", "cache", "queue"}
    assert registry.active_pack_status() == {"active": False, "key": None}


def test_ac022_the_startup_log_reports_that_no_pack_is_active(monkeypatch, caplog) -> None:
    monkeypatch.delenv("CONDITION_PACK_KEY", raising=False)

    with caplog.at_level("INFO", logger="app.pack.registry"):
        registry.log_active_pack()

    assert "no condition pack is active" in caplog.text


def test_ac022_generic_timeline_reads_keep_working_with_no_pack(client, monkeypatch) -> None:
    monkeypatch.delenv("CONDITION_PACK_KEY", raising=False)
    import os

    headers = {"Authorization": f"Bearer {os.getenv('SECRET_KEY', 'x')}"}

    assert client.get("/api/worklist", headers=headers).status_code in (200, 401, 403)


# ------------------------------------------------------------- NFR-019 reloading


def test_nfr019_pack_content_is_reloadable_without_a_deployment(
    tmp_path, monkeypatch, raw: dict
) -> None:
    monkeypatch.setattr(registry, "PACKS_DIR", tmp_path)
    path = tmp_path / "temp_pack.yaml"
    path.write_text(yaml.safe_dump(raw), encoding="utf-8")
    first_key = next(iter(raw["thresholds"]))

    registry.reload()
    before = registry.load_pack("temp_pack").threshold(first_key)

    changed = copy.deepcopy(raw)
    changed["thresholds"][first_key] = float(before) + 0.11
    path.write_text(yaml.safe_dump(changed), encoding="utf-8")
    registry.reload()

    assert registry.load_pack("temp_pack").threshold(first_key) == pytest.approx(
        float(before) + 0.11
    )
