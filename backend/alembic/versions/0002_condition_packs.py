"""Condition packs and their change log.

The axSpA pack is configuration, not code: its code lists, criteria,
counter-evidence rules, thresholds, workup items and patient copy live as
JSONB and are versioned on every save, so a case scored last week can still be
explained by the pack it ran against. `pack_change_log` records who changed
what and when.

Nothing is seeded: the application must start cleanly with no pack active, and
`app.pack.active_pack` answers None until an administrator saves one.

Purely additive: no existing table is touched.

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-16

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "condition_packs",
        sa.Column(
            "id",
            sa.String(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()::text"),
        ),
        sa.Column("pack_key", sa.String(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("config", postgresql.JSONB(), nullable=True),
        sa.Column("awaiting_review", postgresql.JSONB(), nullable=True),
        # No FK to users.id: `users` is created by `Base.metadata.create_all`
        # at app startup, not by a migration, so a migration-time FK to it
        # would fail against a database that has not started the app yet.
        sa.Column("updated_by", sa.String(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        # One row per (pack, version): a save writes the next version rather
        # than editing one, and two writers cannot produce the same version.
        sa.UniqueConstraint("pack_key", "version", name="uq_condition_packs_pack_key_version"),
    )
    op.create_index("ix_condition_packs_pack_key", "condition_packs", ["pack_key"])
    op.create_index(
        "ix_condition_packs_pack_key_version", "condition_packs", ["pack_key", "version"]
    )

    op.create_table(
        "pack_change_log",
        sa.Column(
            "id",
            sa.String(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()::text"),
        ),
        sa.Column("pack_id", sa.String(), sa.ForeignKey("condition_packs.id"), nullable=False),
        sa.Column("changed_by", sa.String(), nullable=True),
        sa.Column(
            "changed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("change_summary", postgresql.JSONB(), nullable=True),
    )
    op.create_index(
        "ix_pack_change_log_pack_id_changed_at", "pack_change_log", ["pack_id", "changed_at"]
    )


def downgrade() -> None:
    op.drop_table("pack_change_log")
    op.drop_table("condition_packs")
