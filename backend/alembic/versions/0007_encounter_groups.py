"""Encounter grouping: events.encounter_group_id (US-004-1).

One EHR row and the claim it generated describe one real visit. The grouping
key is written onto the event rows themselves -- a server-generated UUID per
merged encounter, shared by every contributing row -- so the unified timeline
can return one entry per encounter and count the visit once.

Purely additive: one nullable column plus its index. Nothing is renamed or
dropped, and a row loaded before the de-duplication ran simply has NULL here.

Revision ID: 0007
Revises: 0006
Create Date: 2026-11-22

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "events",
        sa.Column(
            "encounter_group_id",
            sa.String(),
            nullable=True,
            # Server-generated: a row inserted without one still gets a key of
            # its own, so a group is never client-supplied.
            server_default=sa.text("gen_random_uuid()::text"),
        ),
    )
    op.create_index("ix_events_encounter_group_id", "events", ["encounter_group_id"])


def downgrade() -> None:
    op.drop_index("ix_events_encounter_group_id", table_name="events")
    op.drop_column("events", "encounter_group_id")
