"""SQLite engine and session (AD-11 pragmas on every connection)."""

from collections.abc import Iterator
from functools import lru_cache
from pathlib import Path

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session

from roombooker.core.settings import get_settings

PRAGMAS = (
    "PRAGMA journal_mode=WAL",
    "PRAGMA busy_timeout=5000",
    "PRAGMA foreign_keys=ON",
)


def _apply_pragmas(dbapi_connection, _connection_record) -> None:
    cursor = dbapi_connection.cursor()
    try:
        for pragma in PRAGMAS:
            cursor.execute(pragma)
    finally:
        cursor.close()


def make_engine(db_path: Path) -> Engine:
    """Create an engine for `db_path`, creating its parent folder if needed."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{db_path}")
    event.listen(engine, "connect", _apply_pragmas)
    return engine


@lru_cache
def _engine_for(db_path: Path) -> Engine:
    return make_engine(db_path)


def get_engine() -> Engine:
    """The shared engine for the configured database path."""
    return _engine_for(get_settings().db_path)


def get_session() -> Iterator[Session]:
    """FastAPI dependency: one session per request."""
    with Session(get_engine(), expire_on_commit=False) as session:
        yield session
