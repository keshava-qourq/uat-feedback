"""Password hashing: the one place `passlib`'s bcrypt context is configured.

Every account password -- the bootstrap admin, the smoke-test user, and every
password a future login or set-password route handles -- passes through here
and nowhere else, so the hashing scheme is set once and never drifts between
callers.
"""

from passlib.context import CryptContext

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """A salted bcrypt hash of `password`. Never store the password itself."""
    return _pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Whether `password` is the one `password_hash` was made from."""
    return _pwd_context.verify(password, password_hash)
