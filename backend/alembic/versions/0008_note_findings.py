"""Structured free-text clue findings: note_findings (US-015-1).

One row per clue the extractor found in one note, carrying the sentence
exactly as it stands in the note and the note's own source_ref, so every
finding is traceable to the text behind it. A note that yields no finding
writes no row and is marked processed on `notes.processed_at`.

Purely additive: no existing table is touched. The primary key is a
server-generated UUID.

Revision ID: 0008
Revises: 0007
Create Date: 2026-11-23

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    if sa.inspect(op.get_bind()).has_table("note_findings"):
        return
    op.create_table(
        "note_findings",
        sa.Column(
            "id",
            sa.String(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()::text"),
        ),
        sa.Column("note_id", sa.String(), sa.ForeignKey("notes.id"), nullable=False),
        sa.Column("patient_id", sa.String(), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("clue_type", sa.String(), nullable=False),
        sa.Column("finding_value", sa.Text(), nullable=True),
        sa.Column("quoted_sentence", sa.Text(), nullable=False),
        sa.Column("source_ref", sa.String(), nullable=False),
        sa.Column("extractor_model", sa.String(), nullable=False),
        sa.Column(
            "extracted_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_note_findings_note_id", "note_findings", ["note_id"])
    op.create_index(
        "ix_note_findings_patient_id_clue_type", "note_findings", ["patient_id", "clue_type"]
    )


def downgrade() -> None:
    op.drop_table("note_findings")
