"""My bookings: your bookings by day and by week, today highlighted (one test per
distinct behaviour). Reuses the booking tests' fixtures, which pytest finds by name."""
# ruff: noqa: F811 (test arguments name the imported fixtures)

import re
from datetime import UTC, date, datetime, timedelta

from roombooker.core import time as uk
from tests.test_bookings import (  # noqa: F401 (fixtures)
    act,
    book,
    booking_id,
    ids,
    room,
)

LINKS = re.compile(r'class="calendar-booking-link[^"]*" href="/bookings/(\d+)"')
DAY_HEADINGS = re.compile(r'class="calendar-day-heading"[^>]*>([^<]*)<')


def test_shows_bookings_you_organise_and_attend_only(client, act, room, book, ids):
    board, snug = room("Board"), room("Snug")
    mine = booking_id(book("hannah", board, start="09:00", title="Standup"))
    invited = booking_id(
        book("anna", snug, start="11:00", title="Review", attendees=[ids["hannah"]])
    )
    booking_id(book("ben", board, start="13:00", title="Not hers"))

    act("hannah")
    page = client.get("/my-bookings", params={"date": (uk.uk_now().date() + timedelta(days=1))})
    assert page.status_code == 200
    assert [int(i) for i in LINKS.findall(page.text)] == [mine, invited]
    text = re.sub(r"\s+", " ", page.text)
    assert "09:00–10:00</span> <span class=\"booking-title\">Standup" in text
    assert "Board, London" in text and "Snug, London" in text
    assert re.search(r"Standup.*?Organiser.*?Review.*?Attending", text)
    assert "Not hers" not in text


def test_week_runs_monday_to_sunday_by_uk_day(client, act, room, book):
    board = room("Board")
    monday = uk.week_start(uk.uk_now().date() + timedelta(days=14))
    sunday, next_monday = monday + timedelta(days=6), monday + timedelta(days=7)
    late = booking_id(book("hannah", board, day=sunday.isoformat(), start="23:30", length="15"))
    booking_id(book("hannah", board, day=next_monday.isoformat(), start="00:00", length="15"))

    act("hannah")
    thursday = (monday + timedelta(days=3)).isoformat()
    page = client.get("/my-bookings", params={"view": "week", "date": thursday})
    headings = DAY_HEADINGS.findall(page.text)
    assert len(headings) == 7 and headings[0].startswith("Mon") and headings[-1].startswith("Sun")
    assert [int(i) for i in LINKS.findall(page.text)] == [late]
    assert f"Week of Mon {monday.day} {monday:%b}" in page.text
    previous = (monday - timedelta(days=4)).isoformat()
    assert f'href="/my-bookings?view=week&amp;date={previous}"' in page.text
    assert f'href="/my-bookings?view=week&amp;date={next_monday + timedelta(days=3)}"' in page.text


def test_uk_midnight_follows_summer_time():
    assert uk.uk_midnight(date(2027, 7, 1)) == datetime(2027, 6, 30, 23, 0, tzinfo=UTC)
    assert uk.uk_midnight(date(2027, 1, 1)) == datetime(2027, 1, 1, 0, 0, tzinfo=UTC)


def test_today_is_marked(client, act, ids):
    act("hannah")
    today = uk.uk_now().date()
    week = client.get("/my-bookings", params={"view": "week"})
    marked = re.findall(r'aria-current="date">([^<]*)<', week.text)
    assert marked == [f"Today, {today:%a} {today.day} {today:%b}"]
    day = client.get("/my-bookings")
    assert 'class="subtitle calendar-heading is-today" aria-current="date">Today, ' in day.text


def test_bad_view_or_date_shows_today_and_empty_wording(client, act, ids):
    act("hannah")
    page = client.get("/my-bookings", params={"view": "month", "date": "31/12/2026"})
    assert page.status_code == 200
    assert "No bookings today." in page.text
    assert 'href="/my-bookings?view=day' in page.text and 'aria-current="page">Day<' in page.text

    far = uk.week_start(uk.uk_now().date() + timedelta(days=21))
    page = client.get("/my-bookings", params={"view": "week", "date": far.isoformat()})
    assert f"No bookings in the week of Mon {far.day} {far:%b}." in page.text
    assert page.text.count("Nothing booked") == 7
