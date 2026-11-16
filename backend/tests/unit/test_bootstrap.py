"""`app.bootstrap` seeds exactly the two accounts the platform names, and only
when it names them, and never seeds twice."""

from sqlalchemy.orm import Session

from app.bootstrap import seed_bootstrap_accounts
from app.models import User
from app.security import verify_password


def test_seeds_nothing_when_no_platform_variables_are_set(db_session: Session, monkeypatch):
    for var in (
        "BOOTSTRAP_ADMIN_EMAIL",
        "BOOTSTRAP_ADMIN_PASSWORD",
        "SMOKE_TEST_EMAIL",
        "SMOKE_TEST_PASSWORD",
    ):
        monkeypatch.delenv(var, raising=False)

    seed_bootstrap_accounts(db_session)

    assert db_session.query(User).count() == 0


def test_seeds_the_admin_and_smoke_test_users_from_exactly_those_names(
    db_session: Session, monkeypatch
):
    monkeypatch.setenv("BOOTSTRAP_ADMIN_EMAIL", "admin@example.test")
    monkeypatch.setenv("BOOTSTRAP_ADMIN_PASSWORD", "admin-pw-for-test")
    monkeypatch.setenv("SMOKE_TEST_EMAIL", "smoke@example.test")
    monkeypatch.setenv("SMOKE_TEST_PASSWORD", "smoke-pw-for-test")

    seed_bootstrap_accounts(db_session)

    admin = db_session.query(User).filter(User.email == "admin@example.test").one()
    assert admin.role == "admin"
    assert admin.is_active is True
    assert verify_password("admin-pw-for-test", admin.password_hash)

    smoke = db_session.query(User).filter(User.email == "smoke@example.test").one()
    assert smoke.role == "patient"  # the lowest role, per the ticket's instruction
    assert verify_password("smoke-pw-for-test", smoke.password_hash)


def test_is_idempotent_and_never_rehashes_an_existing_users_password(
    db_session: Session, monkeypatch
):
    monkeypatch.setenv("BOOTSTRAP_ADMIN_EMAIL", "admin@example.test")
    monkeypatch.setenv("BOOTSTRAP_ADMIN_PASSWORD", "first-password")
    monkeypatch.delenv("SMOKE_TEST_EMAIL", raising=False)
    monkeypatch.delenv("SMOKE_TEST_PASSWORD", raising=False)

    seed_bootstrap_accounts(db_session)
    first_hash = (
        db_session.query(User).filter(User.email == "admin@example.test").one().password_hash
    )

    # A restart with the platform still naming the same admin must not touch
    # a password an administrator may have since changed.
    monkeypatch.setenv("BOOTSTRAP_ADMIN_PASSWORD", "a-different-password")
    seed_bootstrap_accounts(db_session)

    users = db_session.query(User).filter(User.email == "admin@example.test").all()
    assert len(users) == 1
    assert users[0].password_hash == first_hash
