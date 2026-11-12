"""The only place that reads configuration from the environment."""

import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_DB_PATH = "var/roombooker.db"
DEFAULT_ENV = "local"


@dataclass(frozen=True)
class Settings:
    db_path: Path
    env: str

    @property
    def is_production(self) -> bool:
        return self.env == "production"

    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.db_path}"


def get_settings() -> Settings:
    """Read settings from `ROOMBOOKER_DB_PATH` and `ROOMBOOKER_ENV`."""
    return Settings(
        db_path=Path(os.environ.get("ROOMBOOKER_DB_PATH") or DEFAULT_DB_PATH),
        env=os.environ.get("ROOMBOOKER_ENV") or DEFAULT_ENV,
    )
