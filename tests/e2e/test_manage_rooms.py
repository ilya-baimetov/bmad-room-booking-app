"""The story's verify, in a real browser at laptop (1280x800) and phone (390x844) widths.

The rooms table lives for the whole session, so every test uses rooms with unique names.
"""

import re
import sqlite3
import uuid

import httpx
from playwright.sync_api import Page, expect

from tests.e2e.conftest import pick

REFUSED = "Only office managers can manage rooms."


def unique(label: str) -> str:
    return f"{label} {uuid.uuid4().hex[:6]}"


def person_id(live_server, email: str) -> int:
    return live_server.person_ids()[email][0]


def room_in_db(live_server, name: str) -> tuple[int, int]:
    """(id, is_closed) of the room called `name`, read straight from the database file."""
    with sqlite3.connect(live_server.db_path) as conn:
        return conn.execute("SELECT id, is_closed FROM rooms WHERE name = ?", (name,)).fetchone()


def add_london_room(live_server, name: str) -> int:
    """Anna adds a room with a plain form POST; returns its id."""
    anna = person_id(live_server, "anna.kowalski@example.com")
    with httpx.Client(base_url=live_server.url, cookies={"person_id": str(anna)}) as client:
        assert client.post("/manage-rooms", data={"name": name, "capacity": "8"}).status_code == 303
    return room_in_db(live_server, name)[0]


def row_named(page: Page, name: str):
    """The room row showing `name`, pinned by its id so it can be followed through edits."""
    row = page.locator("tr.room-row").filter(has=page.get_by_text(name, exact=True))
    expect(row).to_have_count(1)
    return page.locator(f"#{row.get_attribute('id')}")


def test_office_manager_lands_on_manage_rooms(page: Page):
    page.goto("/")
    pick(page, "kowal", "Anna Kowalski")

    expect(page).to_have_url(re.compile(r"/manage-rooms$"))
    expect(page.get_by_role("heading", name="Manage rooms")).to_be_visible()
    expect(page.locator(".page .meta")).to_have_text("London")
    tab = page.locator(".top-bar").get_by_role("link", name="Manage rooms")
    expect(tab).to_be_visible()
    expect(tab).to_have_attribute("aria-current", "page")

    page.context.clear_cookies()
    page.goto("/")
    pick(page, "okaf", "Hannah Okafor")
    expect(page.get_by_text("Booking opens soon.")).to_be_visible()
    expect(page.locator(".tabs")).to_have_count(0)

    page.goto("/manage-rooms")  # the direct link
    expect(page.locator("#announce")).to_have_text(REFUSED)
    expect(page.locator(".tabs")).to_have_count(0)


def test_add_edit_close_reopen_without_reload(page: Page):
    page.goto("/")
    pick(page, "kowal", "Anna Kowalski")
    expect(page).to_have_url(re.compile(r"/manage-rooms$"))
    page.evaluate("window.notReloaded = true")
    announce = page.locator("#announce")
    form = page.locator("#add-room")

    name = unique("Huddle")
    form.get_by_label("Room name").fill(name)
    form.get_by_label("Capacity").fill("4")
    form.get_by_role("button", name="Add room").click()
    expect(announce).to_have_text(f"Added {name}.")
    row = row_named(page, name)
    expect(row.locator(".room-status")).to_have_text("Open")
    expect(form.get_by_label("Room name")).to_have_value("")

    # Refused with the reason, keeping the typed values: empty name, capacity 0, duplicate.
    form.get_by_label("Capacity").fill("0")
    form.get_by_role("button", name="Add room").click()
    expect(form.locator(".error-message")).to_have_text(
        re.compile(r"Give the room a name\.\s*Capacity must be a whole number from 1 to 200\.")
    )
    expect(form.get_by_label("Capacity")).to_have_value("0")
    form.get_by_label("Room name").fill(name.upper())
    form.get_by_label("Capacity").fill("6")
    form.get_by_role("button", name="Add room").click()
    expect(form.locator(".error-message")).to_have_text(f"London already has a room called {name}.")
    expect(form.get_by_label("Room name")).to_have_value(name.upper())

    renamed = unique("Focus")
    row.get_by_role("link", name=re.compile("^Edit")).click()
    row.get_by_label("Room name").fill(renamed)
    row.get_by_label("Capacity").fill("10")
    row.get_by_role("button", name="Save").click()
    expect(announce).to_have_text(f"Saved {renamed}.")
    expect(row.locator(".room-name")).to_have_text(renamed)
    expect(row.locator(".room-capacity")).to_have_text("10")

    row.get_by_role("link", name=re.compile("^Close")).click()
    expect(row).to_contain_text(f"Close {renamed}? No one can book it until you reopen it.")
    row.get_by_role("link", name="Keep open").click()
    expect(row.locator(".room-status")).to_have_text("Open")

    row.get_by_role("link", name=re.compile("^Close")).click()
    row.get_by_role("button", name="Close room").click()
    expect(announce).to_have_text(f"Closed {renamed}.")
    expect(row.locator(".room-status")).to_have_text("Closed")
    expect(row).to_have_class(re.compile(r"\bis-closed\b"))

    row.get_by_role("button", name=re.compile("^Reopen")).click()
    expect(announce).to_have_text(f"Reopened {renamed}.")
    expect(row.locator(".room-status")).to_have_text("Open")

    assert page.evaluate("window.notReloaded") is True  # every step was an htmx swap


def test_plain_forms_without_javascript(new_context, live_server, viewport):
    context = new_context(base_url=live_server.url, viewport=viewport, java_script_enabled=False)
    anna = person_id(live_server, "anna.kowalski@example.com")
    context.add_cookies([{"name": "person_id", "value": str(anna), "url": live_server.url}])
    page = context.new_page()
    page.goto("/manage-rooms")
    announce = page.locator("#announce")

    name = unique("Quiet")
    page.locator("#add-room").get_by_label("Room name").fill(name)
    page.locator("#add-room").get_by_label("Capacity").fill("3")
    page.get_by_role("button", name="Add room").click()
    expect(page).to_have_url(re.compile(r"/manage-rooms\?notice=added&room=\d+$"))
    expect(announce).to_have_text(f"Added {name}.")
    row = row_named(page, name)

    renamed = unique("Library")
    row.get_by_role("link", name=re.compile("^Edit")).click()
    expect(page).to_have_url(re.compile(r"/manage-rooms/\d+/edit$"))
    row.get_by_label("Room name").fill(renamed)
    row.get_by_label("Capacity").fill("12")
    row.get_by_role("button", name="Save").click()
    expect(page).to_have_url(re.compile(r"/manage-rooms\?notice=saved&room=\d+$"))
    expect(announce).to_have_text(f"Saved {renamed}.")
    expect(row.locator(".room-capacity")).to_have_text("12")

    row.get_by_role("link", name=re.compile("^Close")).click()
    expect(page).to_have_url(re.compile(r"/manage-rooms/\d+/close$"))
    expect(row).to_contain_text(f"Close {renamed}? No one can book it until you reopen it.")
    row.get_by_role("button", name="Close room").click()
    expect(page).to_have_url(re.compile(r"/manage-rooms\?notice=closed&room=\d+$"))
    expect(announce).to_have_text(f"Closed {renamed}.")
    expect(row.locator(".room-status")).to_have_text("Closed")

    row.get_by_role("button", name=re.compile("^Reopen")).click()
    expect(page).to_have_url(re.compile(r"/manage-rooms\?notice=reopened&room=\d+$"))
    expect(announce).to_have_text(f"Reopened {renamed}.")
    expect(row.locator(".room-status")).to_have_text("Open")


def test_office_manager_of_another_office_is_refused(page: Page, live_server):
    name = unique("Boardroom")
    room_id = add_london_room(live_server, name)

    page.goto("/")
    pick(page, "price", "Joanne Price")
    expect(page).to_have_url(re.compile(r"/manage-rooms$"))
    expect(page.locator(".page .meta")).to_have_text("Manchester")
    expect(page.get_by_text(name, exact=True)).to_have_count(0)

    page.goto(f"/manage-rooms/{room_id}/close")  # the direct link
    expect(page.locator("#announce")).to_have_text(REFUSED)

    response = page.request.post(f"/manage-rooms/{room_id}/close")  # the direct request
    assert response.status == 403
    assert REFUSED in response.text()
    assert room_in_db(live_server, name) == (room_id, 0)
