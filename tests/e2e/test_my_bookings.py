"""My bookings: today marked, a booking opens its details; week columns on a laptop and
day-headed lists on a phone."""

import re
import sqlite3
import uuid
from datetime import timedelta

import httpx
from playwright.sync_api import Page, expect

from roombooker.core import time as uk
from tests.e2e.conftest import pick


def test_week_view_lists_your_booking_and_opens_it(page: Page, live_server, viewport):
    room, title = f"Nook {uuid.uuid4().hex[:6]}", f"Retro {uuid.uuid4().hex[:6]}"
    ids = live_server.person_ids()
    anna, hannah = ids["anna.kowalski@example.com"][0], ids["hannah.okafor@example.com"][0]
    today = uk.uk_now().date()
    tomorrow = today + timedelta(days=1)
    with httpx.Client(base_url=live_server.url, cookies={"person_id": str(anna)}) as client:
        assert client.post("/manage-rooms", data={"name": room, "capacity": "4"}).status_code == 303
        with sqlite3.connect(live_server.db_path) as conn:
            room_id = str(conn.execute("SELECT id FROM rooms WHERE name = ?", (room,)).fetchone()[0])
        booked = client.post(
            "/bookings",
            data={
                "room": room_id,
                "date": tomorrow.isoformat(),
                "start": "14:00",
                "length": "60",
                "title": title,
                "attendee_id": str(hannah),
            },
        )
        assert booked.status_code == 303

    page.goto("/")
    pick(page, "okaf", "Hannah Okafor")
    page.get_by_role("link", name="My bookings").click()
    page.get_by_role("link", name="Week", exact=True).click()

    today_heading = page.locator('[aria-current="date"]')
    expect(today_heading).to_have_text(re.compile(r"^Today, "))
    if uk.week_start(tomorrow) != uk.week_start(today):
        page.get_by_role("link", name="Next week").click()

    days = page.locator(".calendar-day")
    expect(days).to_have_count(7)
    first, second = days.nth(0).bounding_box(), days.nth(1).bounding_box()
    if viewport["width"] >= 768:
        assert first["y"] == second["y"] and second["x"] > first["x"]  # columns
    else:
        assert second["y"] > first["y"] and second["x"] == first["x"]  # stacked lists

    booking = page.get_by_role("link", name=re.compile(rf"14:00–15:00 {title} {room}, London Attending"))
    expect(booking).to_be_visible()
    booking.click()
    expect(page.get_by_role("heading", name=title)).to_be_visible()
    expect(page).to_have_url(re.compile(r"/bookings/\d+$"))
