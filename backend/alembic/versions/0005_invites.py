"""Single-use patient invite links.

One row per issued invite: the token's salted hash (never its plaintext), the
one patient it is scoped to, the role it grants, its expiry and the three
states that refuse it -- opened/consumed/revoked.

Purely additive: no existing table is touched.

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-16

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    if sa.inspect(op.get_bind()).has_table("invites"):
        return
    op.create_table(
        "invites",
        sa.Column(
            "id",
            sa.String(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()::text"),
        ),
        sa.Column("patient_id", sa.String(), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("token_hash", sa.String(), nullable=False, unique=True),
        sa.Column("granted_role", sa.String(), nullable=False, server_default="patient"),
        # A plain string, not an FK: `users` is created by `create_all`, not by
        # a migration -- the same reason `Patient.assigned_clinician_id` is one.
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_invites_token_hash", "invites", ["token_hash"], unique=True)
    op.create_index("ix_invites_patient_id_created_at", "invites", ["patient_id", "created_at"])


def downgrade() -> None:
    op.drop_table("invites")
