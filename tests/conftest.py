"""Shared fixtures: a temporary SQLite file migrated to head through Alembic."""

import sqlite3
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

from roombooker import seed
from roombooker.app import create_app
from roombooker.core import db

ROOT = Path(__file__).resolve().parent.parent
CSV_HEADER = "email,name,office,office_manager"


def migrate_to_head() -> None:
    config = Config(str(ROOT / "alembic.ini"))
    config.attributes["configure_logger"] = False  # keep pytest's log capture intact
    command.upgrade(config, "head")


@pytest.fixture
def db_path(tmp_path, monkeypatch) -> Path:
    path = tmp_path / "var" / "roombooker.db"
    monkeypatch.setenv("ROOMBOOKER_DB_PATH", str(path))
    monkeypatch.delenv("ROOMBOOKER_ENV", raising=False)
    migrate_to_head()
    yield path
    db.get_engine().dispose()
    db._engine_for.cache_clear()


@pytest.fixture
def load_csv(db_path, tmp_path):
    """Write CSV lines (after the header) to a file and run the seed CLI on it."""
    counter = iter(range(1, 1_000))

    def _load(*lines: str, header: str = CSV_HEADER) -> int:
        path = tmp_path / f"people-{next(counter)}.csv"
        path.write_text("\n".join([header, *lines]) + "\n", encoding="utf-8")
        return seed.main([str(path)])

    return _load


@pytest.fixture
def people(db_path):
    """Read the people table as {email: row dict}, straight from the file."""

    def _people() -> dict[str, dict]:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT p.id, p.email, p.name, o.name AS office, p.is_office_manager, p.active "
                "FROM people p JOIN offices o ON o.id = p.home_office_id"
            ).fetchall()
        return {row["email"]: dict(row) for row in rows}

    return _people


@pytest.fixture
def client(db_path) -> TestClient:
    with TestClient(create_app(), follow_redirects=False) as test_client:
        yield test_client
