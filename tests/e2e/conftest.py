"""Browser end-to-end harness: Uvicorn on a temporary database, Playwright at two widths.

The server is started with the README commands (migrate, seed, run), run with this
virtualenv's Python instead of `uv run`, on a free port.
Needs a browser: `uv run playwright install chromium`.
"""

import os
import re
import socket
import sqlite3
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import httpx
import pytest
from playwright.sync_api import Page, expect

ROOT = Path(__file__).resolve().parents[2]
BUILD_SEED = ROOT / "seeds" / "build-people.csv"

VIEWPORTS = {
    "laptop": {"width": 1280, "height": 800},
    "phone": {"width": 390, "height": 844},
}


@dataclass(frozen=True)
class LiveServer:
    url: str
    db_path: Path
    env: dict[str, str]

    def seed(self, csv_path: Path) -> None:
        """Run the seed CLI against the server's database, as a person would."""
        subprocess.run(
            [sys.executable, "-m", "roombooker.seed", str(csv_path)],
            cwd=ROOT,
            env=self.env,
            check=True,
            capture_output=True,
        )

    def person_ids(self) -> dict[str, tuple[int, int]]:
        """{email: (id, active)} read straight from the database file."""
        with sqlite3.connect(self.db_path) as conn:
            return {e: (i, a) for i, e, a in conn.execute("SELECT id, email, active FROM people")}


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture(scope="session")
def live_server(tmp_path_factory):
    db_path = tmp_path_factory.mktemp("e2e") / "var" / "roombooker.db"
    env = {**os.environ, "ROOMBOOKER_DB_PATH": str(db_path)}
    env.pop("ROOMBOOKER_ENV", None)
    port = _free_port()

    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=ROOT, env=env, check=True, capture_output=True,
    )
    server = LiveServer(url=f"http://127.0.0.1:{port}", db_path=db_path, env=env)
    server.seed(BUILD_SEED)

    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "roombooker.app:app", "--port", str(port)],
        cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        deadline = time.monotonic() + 20
        while True:
            try:
                httpx.get(f"{server.url}/pick-name", timeout=1)
                break
            except httpx.TransportError:
                if process.poll() is not None or time.monotonic() > deadline:
                    raise RuntimeError("Uvicorn did not start") from None
                time.sleep(0.1)
        yield server
    finally:
        process.terminate()
        process.wait(timeout=10)


@pytest.fixture(autouse=True)
def build_seed_loaded(live_server):
    """Each test starts with everyone in the build seed active (a reload reactivates)."""
    live_server.seed(BUILD_SEED)


@pytest.fixture(params=list(VIEWPORTS), ids=list(VIEWPORTS))
def viewport(request) -> dict[str, int]:
    return VIEWPORTS[request.param]


@pytest.fixture
def context(new_context, live_server, viewport):
    return new_context(base_url=live_server.url, viewport=viewport)


def pick(page: Page, typed: str, name: str) -> None:
    """On Pick your name: type part of a name, wait for the type-ahead, pick `name`."""
    url_before = page.url
    page.get_by_label("Your name").fill(typed)
    button = page.get_by_role("button", name=re.compile(rf"^{re.escape(name)}\b"))
    expect(button).to_be_visible()
    assert page.url == url_before  # results came by htmx, not a page load
    button.click()
