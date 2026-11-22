"""The evaluation-only label store: patient_labels.

labels.csv was validated and discarded; it is now loaded into a table of its
own, read exclusively through `app.labels`. Two of its columns
(eval_cutoff_date, split) are operational; the rest is ground truth and is
reachable only through the evaluation-only accessor (AC-008/009/010).

Purely additive: no existing table is touched.

Revision ID: 0006
Revises: 0005
Create Date: 2026-11-22

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    if sa.inspect(op.get_bind()).has_table("patient_labels"):
        return
    op.create_table(
        "patient_labels",
        sa.Column(
            "id",
            sa.String(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()::text"),
        ),
        sa.Column("patient_id", sa.String(), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("dataset_version", sa.String(), nullable=False),
        sa.Column("split", sa.String(), nullable=False),
        # A plain date: cutoff comparisons carry no time-of-day or zone.
        sa.Column("eval_cutoff_date", sa.Date(), nullable=True),
        sa.Column("archetype", sa.String(), nullable=True),
        sa.Column("typicality", sa.String(), nullable=True),
        sa.Column("clue_density", sa.Numeric(), nullable=True),
        sa.Column("hla_b27_true", sa.Boolean(), nullable=True),
        sa.Column("axspa_label", sa.Boolean(), nullable=True),
    )
    op.create_index("ix_patient_labels_patient_id", "patient_labels", ["patient_id"])
    op.create_index("ix_patient_labels_dataset_version", "patient_labels", ["dataset_version"])


def downgrade() -> None:
    op.drop_table("patient_labels")
