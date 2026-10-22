"""Migration regression tests for databases touched by older ORM bootstraps."""

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text

from app.config import get_settings
from app.models import AIHourlyBudget


@pytest.fixture()
def migrated_to_0002(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    url = f"sqlite:///{(tmp_path / 'migration_compat.db').as_posix()}"
    monkeypatch.setenv("DATABASE_URL", url)
    get_settings.cache_clear()
    alembic_config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    command.upgrade(alembic_config, "0002_official_provenance")
    engine = create_engine(url)
    try:
        yield engine, alembic_config
    finally:
        engine.dispose()
        get_settings.cache_clear()


def test_0003_accepts_exact_table_precreated_by_legacy_orm(migrated_to_0002):
    engine, config = migrated_to_0002

    # Legacy CLI import/startup created all ORM tables before applying 0003.
    AIHourlyBudget.__table__.create(engine)
    with engine.begin() as connection:
        connection.execute(
            text("INSERT INTO ai_hourly_budget (bucket, window, requests) "
                 "VALUES ('external_llm', '2026102300', 7)")
        )

    command.upgrade(config, "head")
    command.upgrade(config, "head")  # repeated migrations should be harmless

    with engine.connect() as connection:
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "0003_ai_hourly_budget"
        assert connection.scalar(text("SELECT requests FROM ai_hourly_budget")) == 7


def test_0003_rejects_mismatched_preexisting_table(migrated_to_0002):
    engine, config = migrated_to_0002
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE ai_hourly_budget (bucket TEXT PRIMARY KEY, requests INTEGER)"))

    with pytest.raises(RuntimeError, match="manual investigation"):
        command.upgrade(config, "head")

    with engine.connect() as connection:
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "0002_official_provenance"
