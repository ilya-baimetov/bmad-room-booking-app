"""The story's verify, in a real browser at laptop (1280x800) and phone (390x844) widths."""

import re

import httpx
from playwright.sync_api import Page, expect

from tests.e2e.conftest import BUILD_SEED, pick


def top_bar_name(page: Page):
    return page.locator(".top-bar .current-person-name")


def test_readme_commands_serve_pick_your_name(live_server):
    head = httpx.head(f"{live_server.url}/")  # what `curl -sI` sends
    assert head.status_code == 303
    assert head.headers["location"] == "/pick-name?next=/"

    response = httpx.get(f"{live_server.url}/", follow_redirects=True)
    assert response.url.raw_path == b"/pick-name?next=/"
    assert '<h1 class="title">Pick your name</h1>' in response.text


def test_pick_name_shows_in_top_bar_after_reload(page: Page):
    page.goto("/")
    expect(page).to_have_url(re.compile(r"/pick-name\?next=/$"))

    pick(page, "okaf", "Hannah Okafor")

    expect(page).to_have_url(re.compile(r"/$"))
    expect(top_bar_name(page)).to_have_text("Hannah Okafor")
    expect(page.get_by_text("Booking opens soon.")).to_be_visible()
    page.reload()
    expect(top_bar_name(page)).to_have_text("Hannah Okafor")


def test_switch_name_returns_to_same_page(page: Page):
    # Neither is an office manager: since story 2, `/` sends office managers to Manage rooms.
    page.goto("/?from=switch")
    pick(page, "fras", "Chloe Fraser")
    expect(page).to_have_url(re.compile(r"/\?from=switch$"))

    page.locator(".top-bar .current-person").click()
    expect(page.get_by_role("heading", name="Pick your name")).to_be_visible()
    pick(page, "kieran", "Kieran Walsh")

    expect(page).to_have_url(re.compile(r"/\?from=switch$"))
    expect(top_bar_name(page)).to_have_text("Kieran Walsh")


def test_reload_without_person_sends_them_to_pick_your_name(page: Page, live_server, tmp_path):
    page.goto("/")
    pick(page, "adeyemi", "Ben Adeyemi")
    expect(top_bar_name(page)).to_have_text("Ben Adeyemi")
    before = live_server.person_ids()

    lines = BUILD_SEED.read_text(encoding="utf-8").splitlines()
    without_ben = tmp_path / "without-ben.csv"
    without_ben.write_text(
        "\n".join(line for line in lines if not line.startswith("ben.adeyemi@")) + "\n",
        encoding="utf-8",
    )
    live_server.seed(without_ben)

    page.reload()
    expect(page).to_have_url(re.compile(r"/pick-name\?next=/$"))
    page.get_by_label("Your name").fill("adeyemi")
    expect(page.get_by_text("No one called “adeyemi”.")).to_be_visible()

    after = live_server.person_ids()
    assert {e: i for e, (i, _) in after.items()} == {e: i for e, (i, _) in before.items()}
    assert after["ben.adeyemi@example.com"][1] == 0
    assert all(active for e, (_, active) in after.items() if e != "ben.adeyemi@example.com")
