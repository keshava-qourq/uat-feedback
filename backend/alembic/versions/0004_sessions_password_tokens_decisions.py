"""Sign-in tables: users, sessions, password-set tokens and decisions.

Everything sign-in needs, as a migration rather than as `create_all` at
startup: `users` and `sessions` were previously created from the models, so
each table here is created only when it is not already present, and nothing
existing is renamed or dropped.

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-16

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _has(table: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(table)


def upgrade() -> None:
    if not _has("users"):
        op.create_table(
            "users",
            sa.Column(
                "id",
                sa.String(),
                primary_key=True,
                server_default=sa.text("gen_random_uuid()::text"),
            ),
            sa.Column("email", sa.String(), nullable=False, unique=True),
            sa.Column("password_hash", sa.String(), nullable=True),
            sa.Column("role", sa.String(), nullable=False),
            sa.Column("patient_id", sa.String(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("must_set_password", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.Column("deactivated_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_users_email", "users", ["email"], unique=True)

    if not _has("sessions"):
        op.create_table(
            "sessions",
            sa.Column(
                "id",
                sa.String(),
                primary_key=True,
                server_default=sa.text("gen_random_uuid()::text"),
            ),
            sa.Column("user_id", sa.String(), nullable=False),
            sa.Column("token_hash", sa.String(), nullable=False, unique=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.Column(
                "last_seen_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.Column("idle_expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_sessions_token_hash", "sessions", ["token_hash"], unique=True)

    if not _has("password_set_tokens"):
        op.create_table(
            "password_set_tokens",
            sa.Column(
                "id",
                sa.String(),
                primary_key=True,
                server_default=sa.text("gen_random_uuid()::text"),
            ),
            sa.Column("user_id", sa.String(), nullable=False),
            sa.Column("token_hash", sa.String(), nullable=False, unique=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index(
            "ix_password_set_tokens_token_hash",
            "password_set_tokens",
            ["token_hash"],
            unique=True,
        )
        op.create_index("ix_password_set_tokens_user_id", "password_set_tokens", ["user_id"])

    if not _has("decisions"):
        op.create_table(
            "decisions",
            sa.Column(
                "id",
                sa.String(),
                primary_key=True,
                server_default=sa.text("gen_random_uuid()::text"),
            ),
            sa.Column("patient_id", sa.String(), sa.ForeignKey("patients.id"), nullable=False),
            sa.Column("clinician_id", sa.String(), nullable=False),
            sa.Column("decision", sa.String(), nullable=False),
            sa.Column("reason", sa.Text(), nullable=True),
            sa.Column("tier_at_time", sa.String(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.Column("superseded_by", sa.String(), nullable=True),
        )
        op.create_index(
            "ix_decisions_patient_id_created_at", "decisions", ["patient_id", "created_at"]
        )


def downgrade() -> None:
    op.drop_table("decisions")
    op.drop_table("password_set_tokens")
