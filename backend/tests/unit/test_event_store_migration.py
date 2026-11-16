"""US-001-1: the event-store and ingest-tracking migration, run for real.

Each test builds a brand-new PostgreSQL database beside the sandbox's own
(same server, same credentials, a throwaway name), runs `alembic upgrade head`
against it with nothing else done by hand, and inspects the result -- so these
tests prove the migration itself, not the models' `create_all`.
"""

import os
import uuid
from collections.abc import Iterator

import pytest
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url

from alembic import command

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

EXPECTED_TABLES = [
    "patients",
    "events",
    "notes",
    "intake_answers",
    "coverage_periods",
    "encounter_truth",
    "personas",
    "ingest_runs",
    "ingest_file_results",
]

# Each patient-scoped table and the (patient_id, <its time field>) index the
# acceptance criterion requires on it.
EXPECTED_PATIENT_TIME_INDEXES = {
    "events": ["patient_id", "event_time"],
    "notes": ["patient_id", "note_time"],
    "intake_answers": ["patient_id", "answered_at"],
    "coverage_periods": ["patient_id", "start_date"],
    "encounter_truth": ["patient_id", "encounter_time"],
}


@pytest.fixture(scope="module")
def migrated_url() -> Iterator[str]:
    """A fresh database with `alembic upgrade head` applied, dropped afterwards."""
    base_url = os.environ.get("DATABASE_URL", "")
    if not base_url or base_url.startswith("sqlite"):
        pytest.skip("needs the sandbox PostgreSQL in DATABASE_URL")

    url = make_url(base_url)
    db_name = f"mig_test_{uuid.uuid4().hex[:12]}"
    admin = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text(f'CREATE DATABASE "{db_name}"'))
    admin.dispose()

    # render_as_string(hide_password=False): plain str(URL) masks the password.
    target = url.set(database=db_name).render_as_string(hide_password=False)
    config = Config(os.path.join(BACKEND_DIR, "alembic.ini"))
    config.set_main_option("script_location", os.path.join(BACKEND_DIR, "alembic"))
    previous = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = target
    try:
        command.upgrade(config, "head")
        yield target
    finally:
        if previous is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous
        admin = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
        with admin.connect() as conn:
            conn.execute(text(f'DROP DATABASE IF EXISTS "{db_name}" WITH (FORCE)'))
        admin.dispose()


@pytest.mark.parametrize("table", EXPECTED_TABLES)
def test_ac001_migration_creates_every_table(migrated_url: str, table: str) -> None:
    engine = create_engine(migrated_url)
    try:
        assert inspect(engine).has_table(table)
    finally:
        engine.dispose()


@pytest.mark.parametrize("table", EXPECTED_TABLES)
def test_ac001_every_primary_key_is_a_server_generated_uuid(migrated_url: str, table: str) -> None:
    """No row ever supplies its own id: the column defaults to gen_random_uuid()."""
    engine = create_engine(migrated_url)
    try:
        insp = inspect(engine)
        pk = insp.get_pk_constraint(table)["constrained_columns"]
        assert pk == ["id"]
        column = next(c for c in insp.get_columns(table) if c["name"] == "id")
        assert "gen_random_uuid()" in (column["default"] or "")
    finally:
        engine.dispose()


def test_ac001_a_patient_row_gets_its_uuid_from_the_server(migrated_url: str) -> None:
    engine = create_engine(migrated_url)
    try:
        with engine.begin() as conn:
            generated = conn.execute(
                text(
                    "INSERT INTO patients (dataset_patient_id, dataset_version, display_name) "
                    "VALUES ('P-001', 'v1', 'Example') RETURNING id"
                )
            ).scalar_one()
        assert uuid.UUID(generated)
    finally:
        engine.dispose()


@pytest.mark.parametrize(("table", "columns"), sorted(EXPECTED_PATIENT_TIME_INDEXES.items()))
def test_ac002_patient_and_event_time_are_indexed_together(
    migrated_url: str, table: str, columns: list[str]
) -> None:
    engine = create_engine(migrated_url)
    try:
        insp = inspect(engine)
        indexes = [list(ix["column_names"]) for ix in insp.get_indexes(table)]
        assert columns in indexes
    finally:
        engine.dispose()


@pytest.mark.parametrize("table", sorted(EXPECTED_PATIENT_TIME_INDEXES))
def test_ac002_each_patient_scoped_table_has_a_patient_foreign_key(
    migrated_url: str, table: str
) -> None:
    engine = create_engine(migrated_url)
    try:
        fks = inspect(engine).get_foreign_keys(table)
        assert any(
            fk["referred_table"] == "patients" and fk["constrained_columns"] == ["patient_id"]
            for fk in fks
        )
    finally:
        engine.dispose()


def test_ac003_ingest_runs_stores_the_run_summary_columns(migrated_url: str) -> None:
    engine = create_engine(migrated_url)
    try:
        names = {c["name"] for c in inspect(engine).get_columns("ingest_runs")}
        assert {
            "id",
            "dataset_version",
            "seed",
            "status",
            "started_at",
            "finished_at",
            "patient_count",
        } <= names
    finally:
        engine.dispose()


def test_ac003_ingest_file_results_stores_the_per_file_outcome(migrated_url: str) -> None:
    engine = create_engine(migrated_url)
    try:
        insp = inspect(engine)
        names = {c["name"] for c in insp.get_columns("ingest_file_results")}
        assert {
            "ingest_run_id",
            "file_name",
            "status",
            "rows_loaded",
            "rows_rejected",
            "error_detail",
        } <= names
        fks = insp.get_foreign_keys("ingest_file_results")
        assert any(
            fk["referred_table"] == "ingest_runs" and fk["constrained_columns"] == ["ingest_run_id"]
            for fk in fks
        )
    finally:
        engine.dispose()


def test_ac004_dataset_patient_id_is_distinct_from_the_internal_uuid(migrated_url: str) -> None:
    """The source file's id is its own text column, never the primary key."""
    engine = create_engine(migrated_url)
    try:
        columns = {c["name"]: c for c in inspect(engine).get_columns("patients")}
        assert "dataset_patient_id" in columns
        assert "id" in columns
        with engine.begin() as conn:
            new_id = conn.execute(
                text(
                    "INSERT INTO patients (dataset_patient_id, dataset_version, display_name) "
                    "VALUES ('Case-Sensitive-Id', 'v1', 'Example') RETURNING id"
                )
            ).scalar_one()
            stored = conn.execute(
                text("SELECT dataset_patient_id FROM patients WHERE id = :i"), {"i": new_id}
            ).scalar_one()
        assert stored == "Case-Sensitive-Id"
        assert stored != new_id
    finally:
        engine.dispose()
