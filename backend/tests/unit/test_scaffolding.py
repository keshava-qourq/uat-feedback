"""The structural scaffolding every later ticket imports, proved to work.

These are not feature tests: they pin the seams the architecture implies --
settings with working local defaults, a cache that degrades to a miss, a queue
that reports itself unavailable rather than raising into a request, the LLM and
email clients' "not configured" state, the tier vocabulary, the guardrail
result shape and the condition-pack loader's "no pack active" answer.

Nothing here calls Anthropic or SendGrid: the sandbox has no key for either and
a unit test must not depend on a network. Every credential a test needs is
generated at run time.
"""

from __future__ import annotations

import secrets

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app import cache, email, jobs, llm
from app.config import DEFAULT_DEV_ORIGINS, allowed_origins, get_settings, session_secret
from app.database import Base
from app.engine import TIER_HIGH, TIER_INSUFFICIENT_HISTORY, TIER_LOW, TIERS, worklist_rank
from app.guardrails import GuardrailResult
from app.models import ConditionPack
from app.pack import active_pack, pack_is_active


@pytest.fixture
def no_redis(monkeypatch) -> None:
    """The laptop case: Redis is simply not configured."""
    monkeypatch.setenv("REDIS_URL", "")


# ----------------------------------------------------------------------- config


def test_allowed_origins_falls_back_to_the_dev_server(monkeypatch):
    monkeypatch.delenv("ALLOWED_ORIGINS", raising=False)
    assert allowed_origins() == list(DEFAULT_DEV_ORIGINS)


def test_allowed_origins_reads_a_comma_separated_list(monkeypatch):
    monkeypatch.setenv("ALLOWED_ORIGINS", "https://spa.example.test, https://other.example.test")
    assert allowed_origins() == ["https://spa.example.test", "https://other.example.test"]


def test_the_session_secret_is_never_the_public_shared_key(monkeypatch):
    """SECRET_KEY is baked into the frontend bundle, so it must sign nothing."""
    public = secrets.token_urlsafe(16)
    private = secrets.token_urlsafe(16)
    monkeypatch.setenv("SECRET_KEY", public)
    monkeypatch.setenv("JWT_SECRET_KEY", private)

    assert session_secret() == private
    assert session_secret() != public


def test_every_setting_has_a_working_local_default(monkeypatch):
    for name in ("DATABASE_URL", "REDIS_URL", "ALLOWED_ORIGINS", "S3_BUCKET", "MEDIA_ROOT"):
        monkeypatch.delenv(name, raising=False)

    settings = get_settings()

    assert settings.database_url.startswith("sqlite")
    assert settings.redis_url == ""
    assert settings.allowed_origins == DEFAULT_DEV_ORIGINS
    assert settings.s3_configured is False
    assert settings.media_root


# ------------------------------------------------------------------------ cache


def test_the_cache_is_a_miss_rather_than_an_error_without_redis(no_redis):
    name = cache.key("worklist", "nobody")

    assert cache.get_json(name) is None
    assert cache.set_json(name, {"a": 1}) is False
    assert cache.available() is False
    cache.delete(name)  # must not raise
    assert cache.delete_prefix("cache:") == 0


def test_cache_keys_are_namespaced():
    assert cache.key("worklist", "abc").startswith(cache.KEY_PREFIX)


# ------------------------------------------------------------------------ queue


def test_enqueue_reports_an_unavailable_queue_instead_of_a_connection_error(no_redis):
    with pytest.raises(jobs.QueueUnavailable):
        jobs.enqueue(len, "abc")


def test_job_status_never_raises_when_the_queue_is_unreachable(no_redis):
    assert jobs.status("any-id")["status"] == "unavailable"
    assert jobs.available() is False


def test_the_spec_s_job_kinds_are_all_declared():
    for kind in ("ingest", "dedup_check", "extraction", "training", "warm_personas"):
        assert kind in jobs.JOB_KINDS


# ------------------------------------------------------------------ llm / email


def test_the_llm_reports_not_configured_without_a_credential(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)

    assert llm.is_configured() is False
    assert llm.get_client() is None
    assert llm.connection_status() == llm.STATUS_NOT_CONFIGURED


def test_the_llm_reports_connected_with_one(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", secrets.token_urlsafe(16))

    assert llm.is_configured() is True
    assert llm.connection_status() == llm.STATUS_CONNECTED


def test_email_sends_nothing_and_does_not_raise_without_a_credential(monkeypatch):
    monkeypatch.delenv("SENDGRID_API_KEY", raising=False)

    result = email.send(to="patient@example.test", subject="Your link", html="<p>link</p>")

    assert bool(result) is False
    assert result.sent is False
    assert email.get_client() is None
    assert email.connection_status() == email.STATUS_NOT_CONFIGURED


def test_no_credential_value_is_ever_in_a_connection_status(monkeypatch):
    key = secrets.token_urlsafe(16)
    monkeypatch.setenv("ANTHROPIC_API_KEY", key)
    monkeypatch.setenv("SENDGRID_API_KEY", key)

    assert key not in llm.connection_status()
    assert key not in email.connection_status()


# ------------------------------------------------------------------------ tiers


def test_the_worklist_orders_high_moderate_insufficient_low():
    assert worklist_rank(TIER_HIGH) < worklist_rank(TIER_INSUFFICIENT_HISTORY)
    assert worklist_rank(TIER_INSUFFICIENT_HISTORY) < worklist_rank(TIER_LOW)


def test_an_unknown_tier_sorts_last():
    assert worklist_rank("Nonsense") == len(TIERS)
    assert worklist_rank(None) == len(TIERS)


def test_insufficient_history_is_a_tier_not_a_missing_value():
    assert TIER_INSUFFICIENT_HISTORY in TIERS


# ------------------------------------------------------------------- guardrails


def test_a_guardrail_result_is_ok_only_with_no_violations():
    clean = GuardrailResult.passing("post_cutoff")
    assert clean.ok is True and clean.count == 0

    failed = clean.with_violation("/api/cases/1", "an item dated after the cutoff")
    assert failed.ok is False
    assert failed.count == 1
    assert failed.violations[0].guardrail == "post_cutoff"


# ------------------------------------------------------------------------- pack


@pytest.fixture
def pack_db() -> Session:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, expire_on_commit=False)()


def test_the_app_runs_with_no_pack_active(pack_db: Session):
    """A fresh database has no pack, and that is a supported state, not an error."""
    assert active_pack(pack_db) is None
    assert pack_is_active(pack_db) is False


def test_the_active_pack_is_the_enabled_one_of_highest_version(pack_db: Session):
    pack_db.add(ConditionPack(pack_key="axspa", version=1, enabled=True, config={"a": 1}))
    pack_db.add(ConditionPack(pack_key="axspa", version=2, enabled=True, config={"a": 2}))
    # A newer draft that is not enabled must not win.
    pack_db.add(ConditionPack(pack_key="axspa", version=3, enabled=False, config={"a": 3}))
    pack_db.commit()

    pack = active_pack(pack_db)

    assert pack is not None
    assert pack.version == 2
    assert pack.section("a") == 2
    assert pack.section("not-there", []) == []
