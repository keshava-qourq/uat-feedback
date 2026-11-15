"""Unified event store and ingest-run tracking tables.

Adds patients, events, notes, intake_answers, coverage_periods,
encounter_truth, personas, ingest_runs and ingest_file_results. Every primary
key is a server-generated UUID (`gen_random_uuid()`, built into PostgreSQL 16
core -- no extension needed). Purely additive: no existing table is touched.

Revision ID: 0001
Revises:
Create Date: 2026-11-15

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "patients",
        sa.Column(
            "id",
            sa.String(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()::text"),
        ),
        sa.Column("dataset_patient_id", sa.String(), nullable=False),
        sa.Column("dataset_version", sa.String(), nullable=False),
        sa.Column("display_name", sa.String(), nullable=False),
        sa.Column("birth_year", sa.Integer(), nullable=True),
        sa.Column("sex", sa.String(), nullable=True),
        sa.Column("reachable_history_start", sa.Date(), nullable=True),
        # No FK to users.id: `users` is created by `Base.metadata.create_all`
        # at app startup (see app.models' module docstring), not by a
        # migration, so a migration-time FK to it would fail against a fresh
        # database that has not started the app yet.
        sa.Column("assigned_clinician_id", sa.String(), nullable=True),
    )
    op.create_index("ix_patients_dataset_patient_id", "patients", ["dataset_patient_id"])

    op.create_table(
        "events",
        sa.Column(
            "id",
            sa.String(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()::text"),
        ),
        sa.Column("patient_id", sa.String(), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("source_event_id", sa.String(), nullable=False),
        sa.Column("event_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("code_system", sa.String(), nullable=True),
        sa.Column("code", sa.String(), nullable=True),
        sa.Column("display", sa.String(), nullable=True),
        sa.Column("value", sa.Text(), nullable=True),
        sa.Column("unit", sa.String(), nullable=True),
        sa.Column("provider_org", sa.String(), nullable=True),
        sa.Column("provider_specialty", sa.String(), nullable=True),
        sa.Column("source_type", sa.String(), nullable=False),
        sa.Column("source_ref", sa.String(), nullable=False),
        sa.Column("encounter_ref", sa.String(), nullable=True),
        sa.Column("confidence", sa.Numeric(), nullable=True),
        sa.Column("dataset_version", sa.String(), nullable=False),
    )
    op.create_index("ix_events_patient_id_event_time", "events", ["patient_id", "event_time"])

    op.create_table(
        "notes",
        sa.Column(
            "id",
            sa.String(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()::text"),
        ),
        sa.Column("patient_id", sa.String(), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("source_ref", sa.String(), nullable=False),
        sa.Column("note_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("note_type", sa.String(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_notes_patient_id_note_time", "notes", ["patient_id", "note_time"])

    op.create_table(
        "intake_answers",
        sa.Column(
            "id",
            sa.String(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()::text"),
        ),
        sa.Column("patient_id", sa.String(), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("question_key", sa.String(), nullable=False),
        sa.Column("answer_value", sa.JSON(), nullable=False),
        sa.Column("answered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("event_id", sa.String(), sa.ForeignKey("events.id"), nullable=True),
        sa.Column("is_complete", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index(
        "ix_intake_answers_patient_id_answered_at",
        "intake_answers",
        ["patient_id", "answered_at"],
    )

    op.create_table(
        "coverage_periods",
        sa.Column(
            "id",
            sa.String(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()::text"),
        ),
        sa.Column("patient_id", sa.String(), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("payer", sa.String(), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("gap_reason", sa.String(), nullable=True),
    )
    op.create_index(
        "ix_coverage_periods_patient_id_start_date",
        "coverage_periods",
        ["patient_id", "start_date"],
    )

    op.create_table(
        "encounter_truth",
        sa.Column(
            "id",
            sa.String(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()::text"),
        ),
        sa.Column("patient_id", sa.String(), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("true_encounter_id", sa.String(), nullable=False),
        sa.Column("encounter_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("visible_in_sources", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("matched_encounter_id", sa.String(), nullable=True),
    )
    op.create_index(
        "ix_encounter_truth_patient_id_encounter_time",
        "encounter_truth",
        ["patient_id", "encounter_time"],
    )

    op.create_table(
        "personas",
        sa.Column(
            "id",
            sa.String(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()::text"),
        ),
        sa.Column("persona_key", sa.String(), nullable=False, unique=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("one_line_description", sa.Text(), nullable=False),
        sa.Column("patient_id", sa.String(), sa.ForeignKey("patients.id"), nullable=False),
        sa.Column("expected_outcome", sa.JSON(), nullable=True),
    )
    op.create_index("ix_personas_persona_key", "personas", ["persona_key"], unique=True)

    op.create_table(
        "ingest_runs",
        sa.Column(
            "id",
            sa.String(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()::text"),
        ),
        sa.Column("dataset_version", sa.String(), nullable=False),
        sa.Column("seed", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("patient_count", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "ingest_file_results",
        sa.Column(
            "id",
            sa.String(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()::text"),
        ),
        sa.Column("ingest_run_id", sa.String(), sa.ForeignKey("ingest_runs.id"), nullable=False),
        sa.Column("file_name", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("rows_loaded", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rows_rejected", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_detail", sa.Text(), nullable=True),
    )
    op.create_index(
        "ix_ingest_file_results_ingest_run_id", "ingest_file_results", ["ingest_run_id"]
    )


def downgrade() -> None:
    op.drop_table("ingest_file_results")
    op.drop_table("ingest_runs")
    op.drop_table("personas")
    op.drop_table("encounter_truth")
    op.drop_table("coverage_periods")
    op.drop_table("intake_answers")
    op.drop_table("notes")
    op.drop_table("events")
    op.drop_table("patients")
