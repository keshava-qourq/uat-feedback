"""Seeds the two accounts the platform always provides, once, at startup.

The deployed API always has `BOOTSTRAP_ADMIN_EMAIL`/`BOOTSTRAP_ADMIN_PASSWORD`
set, and `SMOKE_TEST_EMAIL`/`SMOKE_TEST_PASSWORD` besides -- this sandbox's
Playwright runner relies on the same two (see `frontend/e2e/support/admin.ts`).
Locally and in the unit-test run none of the four is set, and this module
seeds nothing: an empty `users` table is the correct state there.

Both accounts are seeded idempotently -- a user already present with that
email is left exactly as it is, including its password, so a restart never
re-hashes a password an administrator has since changed. The admin account
gets this architecture's highest role; the smoke-test account gets its
lowest, patient, exactly as the product's own role split demands (NFR-012:
no patient-role account carries more than a patient can see).
"""

import os

from sqlalchemy.orm import Session

from app.models import User
from app.security import hash_password

ADMIN_ROLE = "admin"
SMOKE_TEST_ROLE = "patient"


def _ensure_user(db: Session, *, email: str, password: str, role: str) -> None:
    exists = db.query(User.id).filter(User.email == email).first() is not None
    if exists:
        return
    db.add(
        User(
            email=email,
            password_hash=hash_password(password),
            role=role,
            is_active=True,
            # Seeded with a real, working password already: nobody has to
            # chase a first-sign-in link to use the account the platform
            # just told us about.
            must_set_password=False,
        )
    )
    db.commit()


def seed_bootstrap_accounts(db: Session) -> None:
    """Create the admin and/or smoke-test user, only when the platform named them."""
    admin_email = os.getenv("BOOTSTRAP_ADMIN_EMAIL")
    admin_password = os.getenv("BOOTSTRAP_ADMIN_PASSWORD")
    if admin_email and admin_password:
        _ensure_user(db, email=admin_email, password=admin_password, role=ADMIN_ROLE)

    smoke_email = os.getenv("SMOKE_TEST_EMAIL")
    smoke_password = os.getenv("SMOKE_TEST_PASSWORD")
    if smoke_email and smoke_password:
        _ensure_user(db, email=smoke_email, password=smoke_password, role=SMOKE_TEST_ROLE)
