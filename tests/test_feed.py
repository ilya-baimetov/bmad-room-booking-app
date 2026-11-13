"""Each person's private calendar feed and resetting its address (one test per distinct
behaviour). Reuses the booking tests' fixtures, which pytest finds by name."""
# ruff: noqa: F811 (test arguments name the imported fixtures)

import re
import secrets
import sqlite3
from datetime import date, time, timedelta

from alembic import command
from alembic.config import Config

from roombooker.core import time as uk
from tests.conftest import ROOT
from tests.test_bookings import (  # noqa: F401 (fixtures)
    PEOPLE,
    act,
    book,
    booking_id,
    ics_lines,
    ids,
    insert_booking,
    room,
    table,
    uk_day,
)

FEED_URL = re.compile(r'id="feed-url"[^>]*value="(http://testserver/feeds/([A-Za-z0-9_-]{43})\.ics)"')
UID = re.compile(r"UID:booking-(\d+)-([0-9a-f]{8})@roombooker")


def create_feed(client, replace: bool = False) -> str:
    """Press Create feed address (or, with `replace`, confirm Reset) as the current
    person; returns the feed's path."""
    response = client.post("/my-bookings/feed", data={"replace": "1"} if replace else {})
    assert response.status_code == 303
    notice = "feed-reset" if replace else "feed-created"
    assert response.headers["location"] == f"/my-bookings?notice={notice}"
    page = client.get(response.headers["location"])
    return "/feeds/" + FEED_URL.search(page.text)[2] + ".ics"


def fetch(client, path: str):
    """Fetch the feed as a calendar app would: no cookie."""
    saved = dict(client.cookies)
    client.cookies.clear()
    try:
        return client.get(path)
    finally:
        for name, value in saved.items():
            client.cookies.set(name, value)


def assert_not_found(response) -> None:
    assert response.status_code == 404
    assert response.headers["content-type"].startswith("text/plain")
    assert "BEGIN:VCALENDAR" not in response.text


def uids(response) -> list[int]:
    return [int(m[1]) for m in UID.finditer(response.text)]


def utc(day: str, clock: str) -> str:
    return uk.ical_utc(uk.uk_to_utc(date.fromisoformat(day), time.fromisoformat(clock)))


def test_subscribed_feed_has_organised_and_attended_bookings_only(
    client, act, room, book, ids, insert_booking
):
    board, snug = room("Board"), room("Snug")
    a = booking_id(book("hannah", board, start="09:00", title="Standup"))
    b = booking_id(book("anna", snug, start="11:00", title="Review", attendees=[ids["hannah"]]))
    booking_id(book("ben", board, start="13:00", title="Not hers"))
    now = uk.utc_now().replace(second=0, microsecond=0)
    old_end = now - timedelta(days=31)
    insert_booking(  # ended 31 days ago
        snug, ids["hannah"], uk.to_text(old_end - timedelta(hours=1)), uk.to_text(old_end)
    )
    recent_end = now - timedelta(days=29)
    recent = insert_booking(  # ended 29 days ago: still in the feed
        snug, ids["hannah"], uk.to_text(recent_end - timedelta(hours=1)), uk.to_text(recent_end)
    )

    act("hannah")
    path = create_feed(client)
    response = fetch(client, path)

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/calendar; charset=utf-8"
    assert response.headers["cache-control"] == "private, no-cache"
    assert uids(response) == [recent, a, b]
    lines = ics_lines(response.text)
    assert lines[:8] == [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Room booker//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:Room bookings",
        "REFRESH-INTERVAL;VALUE=DURATION:PT1H",
        "X-PUBLISHED-TTL:PT1H",
    ]
    assert f"DTSTART:{utc(uk_day(1), '09:00')}" in lines
    assert f"DTEND:{utc(uk_day(1), '10:00')}" in lines
    assert "Not hers" not in response.text
    assert "ATTENDEE" not in response.text and "ORGANIZER" not in response.text
    assert fetch(client, path).status_code == 200
    head = client.head(path)
    assert head.status_code == 200 and head.text == ""


def test_cancelled_booking_leaves_the_feed(client, act, room, book):
    snug = room("Snug")
    a = booking_id(book("hannah", snug))
    path = create_feed(client)
    assert uids(fetch(client, path)) == [a]
    assert client.post(f"/bookings/{a}/cancel").status_code == 303
    assert uids(fetch(client, path)) == []


def test_closing_a_room_removes_its_bookings_from_the_feed(client, act, room, book, ids):
    snug, board = room("Snug"), room("Board")
    a = booking_id(book("ben", snug, attendees=[ids["hannah"]]))
    kept = booking_id(book("hannah", board))
    act("hannah")
    path = create_feed(client)
    assert uids(fetch(client, path)) == [a, kept]
    act("anna")
    assert client.post(f"/manage-rooms/{snug}/close").status_code == 303
    assert uids(fetch(client, path)) == [kept]


def test_reset_retires_the_old_address(client, act, room, book, table, ids):
    a = booking_id(book("hannah", room("Snug")))
    old = create_feed(client)

    confirm = client.get("/my-bookings/feed/reset")
    assert confirm.status_code == 200
    assert '<form class="confirm" method="post" action="/my-bookings/feed">' in confirm.text
    assert 'href="/my-bookings" autofocus>Keep address</a>' in confirm.text
    assert '<input type="hidden" name="replace" value="1">' in confirm.text
    new = create_feed(client, replace=True)
    page = client.get("/my-bookings?notice=feed-reset")
    assert "Your feed address has been reset. The old address has stopped working." in page.text

    assert new != old
    assert_not_found(fetch(client, old))
    assert uids(fetch(client, new)) == [a]
    assert table("SELECT feed_token FROM people WHERE id = ?", ids["hannah"]) == [
        (new.removeprefix("/feeds/").removesuffix(".ics"),)
    ]


def test_unknown_or_malformed_token_is_404_without_writes(client, act, ids, db_path):
    act("hannah")
    create_feed(client)
    with sqlite3.connect(db_path) as conn:
        before = conn.execute("SELECT id, feed_token FROM people ORDER BY id").fetchall()
    for path in (
        f"/feeds/{secrets.token_urlsafe(32)}.ics",
        "/feeds/abc.ics",
        "/feeds/..%2Fx.ics",
        "/feeds/..%2F" + "a" * 40 + ".ics",  # 43 characters, but not all URL-safe
        "/feeds/" + "a" * 43,  # no .ics
        "/feeds/" + "a" * 42 + "!.ics",
    ):
        assert_not_found(fetch(client, path))
    # Clients resolve a literal `..` before sending (`/x.ics`), so it never reaches a feed.
    assert fetch(client, "/feeds/../x.ics").status_code == 404
    with sqlite3.connect(db_path) as conn:
        assert conn.execute("SELECT id, feed_token FROM people ORDER BY id").fetchall() == before


def test_inactive_persons_feed_is_404(client, act, room, book, load_csv):
    booking_id(book("hannah", room("Snug")))
    path = create_feed(client)
    assert fetch(client, path).status_code == 200
    assert load_csv(*(line for line in PEOPLE if not line.startswith("hannah"))) == 0
    assert_not_found(fetch(client, path))


def test_no_address_until_created(client, act, ids, table):
    act("hannah")
    page = client.get("/my-bookings")
    assert page.status_code == 200
    assert '<form method="post" action="/my-bookings/feed">' in page.text
    assert ">Create feed address</button>" in page.text
    assert 'id="feed-url"' not in page.text and "Reset address" not in page.text
    client.head("/my-bookings")
    client.get("/my-bookings", params={"view": "week"})
    assert client.get("/my-bookings/feed/reset").headers["location"] == "/my-bookings"
    assert table("SELECT COUNT(*) FROM people WHERE feed_token IS NOT NULL") == [(0,)]

    create_feed(client)
    page = client.get("/my-bookings?notice=feed-created")
    assert "Your calendar feed address is ready." in page.text
    assert "stopped working" not in page.text
    assert 'readonly onfocus="this.select()"' in page.text
    assert 'href="/my-bookings/feed/reset">Reset address</a>' in page.text
    assert "Create feed address" not in page.text
    assert table("SELECT COUNT(*) FROM people WHERE feed_token IS NOT NULL") == [(1,)]


def test_stale_create_goes_to_the_confirmation_without_replacing(client, act, ids, table):
    act("hannah")
    path = create_feed(client)
    token = path.removeprefix("/feeds/").removesuffix(".ics")
    response = client.post("/my-bookings/feed")  # Create pressed on a stale page
    assert response.status_code == 303
    assert response.headers["location"] == "/my-bookings/feed/reset"
    assert table("SELECT feed_token FROM people WHERE id = ?", ids["hannah"]) == [(token,)]
    assert fetch(client, path).status_code == 200


def test_without_a_cookie_my_bookings_and_reset_pick_a_name_first(client, ids, table):
    for method, path in (
        ("GET", "/my-bookings"),
        ("GET", "/my-bookings/feed/reset"),
        ("POST", "/my-bookings/feed"),
    ):
        response = client.request(method, path)
        assert response.status_code == 303
        assert response.headers["location"].startswith("/pick-name?next=")
    assert table("SELECT COUNT(*) FROM people WHERE feed_token IS NOT NULL") == [(0,)]


def test_my_bookings_shows_only_the_viewers_address(client, act, ids):
    act("hannah")
    hannahs = create_feed(client)
    act("ben")
    page = client.get("/my-bookings")
    assert hannahs.removeprefix("/feeds/").removesuffix(".ics") not in page.text
    assert "Create feed address" in page.text
    bens = create_feed(client)
    assert FEED_URL.search(client.get("/my-bookings").text)[1] == f"http://testserver{bens}"
    assert hannahs != bens


def test_reused_booking_id_gets_a_different_uid(client, act, room, book):
    snug = room("Snug")
    first = booking_id(book("hannah", snug, title="Planning"))
    path = create_feed(client)
    first_uid = UID.search(fetch(client, path).text)[0]
    assert client.post(f"/bookings/{first}/cancel").status_code == 303
    again = booking_id(book("hannah", snug, title="Retro"))
    assert again == first  # SQLite reuses the highest id after a delete
    second_uid = UID.search(fetch(client, path).text)[0]
    assert second_uid != first_uid
    assert second_uid.startswith(f"UID:booking-{again}-")


def test_download_differs_from_story_1_only_in_the_uid(client, act, room, book):
    a = booking_id(book("hannah", room("Snug"), attendees=()))
    lines = ics_lines(client.get(f"/bookings/{a}/calendar.ics").text)
    uid_lines = [line for line in lines if line.startswith("UID:")]
    assert len(uid_lines) == 1 and UID.fullmatch(uid_lines[0])[1] == str(a)
    stamp = next(line for line in lines if line.startswith("DTSTAMP:"))
    assert lines == [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Room booker//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "BEGIN:VEVENT",
        uid_lines[0],
        stamp,
        f"DTSTART:{utc(uk_day(1), '10:00')}",
        f"DTEND:{utc(uk_day(1), '11:00')}",
        "SUMMARY:Planning",
        "LOCATION:Snug\\, London",
        "DESCRIPTION:Booked by Hannah Okafor",
        "STATUS:CONFIRMED",
        "END:VEVENT",
        "END:VCALENDAR",
        "",
    ]
    feed = ics_lines(fetch(client, create_feed(client)).text)
    assert uid_lines[0] in feed  # the same event in the download and the feed


def test_migration_downgrade_and_upgrade_round_trip(db_path, table, ids):
    config = Config(str(ROOT / "alembic.ini"))
    config.attributes["configure_logger"] = False
    columns = "SELECT name FROM pragma_table_info('people')"
    assert ("feed_token",) in table(columns)
    command.downgrade(config, "0003")
    assert ("feed_token",) not in table(columns)
    assert table("SELECT name FROM sqlite_master WHERE name = 'uq_people_feed_token'") == []
    command.upgrade(config, "head")
    assert ("feed_token",) in table(columns)
    assert table("SELECT COUNT(*) FROM people WHERE feed_token IS NULL") == [(len(PEOPLE),)]
    with sqlite3.connect(db_path) as conn:  # many NULLs allowed, duplicates refused
        conn.execute("UPDATE people SET feed_token = 'x' WHERE id = ?", (ids["anna"],))
        try:
            conn.execute("UPDATE people SET feed_token = 'x' WHERE id = ?", (ids["ben"],))
        except sqlite3.IntegrityError:
            pass
        else:
            raise AssertionError("duplicate feed_token accepted")
