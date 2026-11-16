"""Per-file provenance-failure counter on an ingest run's file results.

A row of events.csv with no source_type or source_ref (or a source_type
outside ehr|claim|patient) is never inserted: it is counted here, beside
rows_loaded/rows_rejected, so the ingest report names the failure loudly
rather than letting an unsourced event reach scoring or a screen.

Purely additive: one nullable-free column with a server default of 0, so an
existing row keeps a valid value.

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-16

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "ingest_file_results",
        sa.Column(
            "provenance_failures",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.create_index("ix_events_source_ref", "events", ["source_ref"])
    op.create_index("ix_notes_source_ref", "notes", ["source_ref"])


def downgrade() -> None:
    op.drop_index("ix_notes_source_ref", table_name="notes")
    op.drop_index("ix_events_source_ref", table_name="events")
    op.drop_column("ingest_file_results", "provenance_failures")
