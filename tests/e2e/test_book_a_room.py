"""Find a free room, book it with an attendee, see it, cancel it, book it again: laptop and phone widths."""

import re
import sqlite3
import uuid
from datetime import timedelta

import httpx
from playwright.sync_api import Page, expect

from roombooker.core import time as uk
from tests.e2e.conftest import pick


def test_find_book_and_cancel(page: Page, live_server):
    room = f"Studio {uuid.uuid4().hex[:6]}"
    anna = live_server.person_ids()["anna.kowalski@example.com"][0]
    with httpx.Client(base_url=live_server.url, cookies={"person_id": str(anna)}) as client:
        assert client.post("/manage-rooms", data={"name": room, "capacity": "6"}).status_code == 303
    tomorrow = (uk.uk_now().date() + timedelta(days=1)).isoformat()

    page.goto("/")
    pick(page, "okaf", "Hannah Okafor")
    expect(page).to_have_url(re.compile(r"/rooms$"))

    page.get_by_label("Date").fill(tomorrow)
    page.get_by_label("Start").select_option("10:00")
    page.get_by_label("Length").select_option("60")
    page.get_by_label("People").fill("6")
    page.get_by_role("button", name="Find rooms").click()
    book = page.get_by_role("link", name=f"Book {room}, London")
    expect(book).to_be_visible()
    book.click()

    expect(page.get_by_role("heading", name=f"Book {room}")).to_be_visible()
    expect(page.get_by_label("Title")).to_have_value("Hannah Okafor's meeting")
    page.get_by_label("Title").fill("Design review")
    page.get_by_label("Add a person").fill("adey")
    page.get_by_role("button", name=re.compile(r"^Add Ben Adeyemi")).click()  # came by htmx
    expect(page.get_by_role("button", name="Remove Ben Adeyemi")).to_be_visible()
    expect(page.get_by_label("Title")).to_have_value("Design review")
    page.get_by_role("button", name="Book", exact=True).click()

    expect(page.locator("#announce")).to_have_text(f"Booked. {room}, 10:00–11:00.")
    expect(page.get_by_role("heading", name="Design review")).to_be_visible()
    expect(page.get_by_text("Ben Adeyemi")).to_be_visible()

    page.get_by_role("link", name="Cancel booking").click()
    expect(page.get_by_text("Cancel this booking?")).to_be_visible()
    page.get_by_role("button", name="Cancel booking").click()
    expect(page).to_have_url(re.compile(r"/rooms\?notice=cancelled$"))
    expect(page.locator("#announce")).to_have_text("Booking cancelled.")


def test_book_again_when_next_week_is_taken(page: Page, live_server):
    room = f"Den {uuid.uuid4().hex[:6]}"
    ids = {email.split(".")[0]: i for email, (i, _) in live_server.person_ids().items()}
    today = uk.uk_now().date()
    tomorrow = (today + timedelta(days=1)).isoformat()
    next_week = (today + timedelta(days=8)).isoformat()

    def as_person(who: str) -> httpx.Client:
        return httpx.Client(base_url=live_server.url, cookies={"person_id": str(ids[who])})

    with as_person("anna") as client:
        assert client.post("/manage-rooms", data={"name": room, "capacity": "6"}).status_code == 303
    with sqlite3.connect(live_server.db_path) as conn:
        room_id = conn.execute("SELECT id FROM rooms WHERE name = ?", (room,)).fetchone()[0]
    booking = {"room": room_id, "start": "10:00", "length": "60"}
    with as_person("anna") as client:  # next week's 10:00-10:30 is taken
        taken = {**booking, "date": next_week, "length": "30", "title": "Taken"}
        assert client.post("/bookings", data=taken).status_code == 303
    with as_person("hannah") as client:
        first = {**booking, "date": tomorrow, "title": "Weekly sync", "attendee_id": ids["ben"]}
        response = client.post("/bookings", data=first)
        assert response.status_code == 303
        details = response.headers["location"].split("?")[0]

    page.goto("/")
    pick(page, "okaf", "Hannah Okafor")
    page.goto(details)
    page.get_by_role("link", name="Book again").click()

    expect(page.get_by_role("heading", name=f"Book {room}")).to_be_visible()
    expect(page.locator("#announce")).to_have_text(
        f"Someone has already booked {room} at that time. Pick another time."
    )
    expect(page.get_by_label("Date")).to_have_value(next_week)
    expect(page.get_by_label("Title")).to_have_value("Weekly sync")
    page.get_by_label("Start").select_option("11:00")
    page.get_by_role("button", name="Check time").click()

    expect(page.locator("#announce")).to_have_text("")
    expect(page.get_by_label("Title")).to_have_value("Weekly sync")
    expect(page.get_by_role("button", name="Remove Ben Adeyemi")).to_be_visible()
    page.get_by_role("button", name="Book", exact=True).click()

    expect(page.locator("#announce")).to_have_text(f"Booked. {room}, 11:00–12:00.")
    expect(page.get_by_role("heading", name="Weekly sync")).to_be_visible()
    expect(page.get_by_text("Ben Adeyemi")).to_be_visible()
