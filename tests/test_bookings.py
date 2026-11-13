"""Find a free room, book it, see it, cancel it (one test per distinct behaviour).

Times are relative to the real clock: the close-room trigger uses SQLite's own "now".
"""

import logging
import re
import sqlite3
import threading
from datetime import date, time, timedelta

import pytest
from sqlalchemy.orm import Session

from roombooker.bookings import service
from roombooker.core import db
from roombooker.core import time as uk
from roombooker.people import service as people_service

PEOPLE = (
    "anna@example.com,Anna Kowalski,London,true",
    "ben@example.com,Ben Adeyemi,London,",
    "hannah@example.com,Hannah Okafor,London,",
    "joanne@example.com,Joanne Price,Manchester,true",
    "kieran@example.com,Kieran Walsh,Manchester,",
)
ANNOUNCE = re.compile(r'<div id="announce"[^>]*>(.*?)</div>', re.S)
OFFICE_NAMES = re.compile(r'class="office-name"[^>]*>([^<]*)<')
FREE_ROOMS = re.compile(r'<li class="free-room">\s*<span class="room-name">([^<]*)<')


def uk_day(days_ahead: int) -> str:
    return (uk.uk_now().date() + timedelta(days=days_ahead)).isoformat()


@pytest.fixture
def ids(load_csv, people):
    assert load_csv(*PEOPLE) == 0
    return {email.split("@")[0]: row["id"] for email, row in people().items()}


@pytest.fixture
def act(client, ids):
    def _act(who: str) -> None:
        client.cookies.set("person_id", str(ids[who]))

    return _act


@pytest.fixture
def room(client, act, db_path):
    """Add a room through Manage rooms as that office's manager; returns its id."""

    def _room(name: str, capacity: int = 8, manager: str = "anna", closed: bool = False) -> int:
        act(manager)
        assert client.post(
            "/manage-rooms", data={"name": name, "capacity": str(capacity)}
        ).status_code == 303
        with sqlite3.connect(db_path) as conn:
            room_id = conn.execute("SELECT id FROM rooms WHERE name = ?", (name,)).fetchone()[0]
        if closed:
            client.post(f"/manage-rooms/{room_id}/close")
        return room_id

    return _room


@pytest.fixture
def book(client, act):
    """POST a booking as someone; returns the response."""

    def _book(who, room_id, day=None, start="10:00", length="60", title="Planning", attendees=()):
        act(who)
        return client.post(
            "/bookings",
            data={
                "room": str(room_id),
                "date": day or uk_day(1),
                "start": start,
                "length": length,
                "title": title,
                "attendee_id": [str(a) for a in attendees],
            },
        )

    return _book


def booking_id(response) -> int:
    assert response.status_code == 303, response.text
    return int(re.fullmatch(r"/bookings/(\d+)\?notice=booked", response.headers["location"])[1])


@pytest.fixture
def table(db_path):
    def _table(sql: str, *args) -> list[tuple]:
        with sqlite3.connect(db_path) as conn:
            return conn.execute(sql, args).fetchall()

    return _table


def test_free_rooms_own_office_first_with_capacity_filter(client, act, room, book):
    room("Snug", 2)
    board = room("Board", 10)
    room("Attic", 6, closed=True)
    room("Hub", 6, manager="joanne")
    room("Den", 12, manager="joanne")
    book("anna", board, start="10:30", length="30", title="Budget")

    act("kieran")  # Manchester first for Kieran
    page = client.get("/rooms", params={"date": uk_day(1), "start": "10:00", "length": "60"})
    assert page.status_code == 200
    assert OFFICE_NAMES.findall(page.text) == ["Manchester ", "London"]
    assert FREE_ROOMS.findall(page.text) == ["Den", "Hub", "Snug"]  # Board taken, Attic closed
    assert "Budget" in page.text and "Booked by Anna Kowalski" in page.text  # booked then

    act("hannah")
    page = client.get(
        "/rooms", params={"date": uk_day(1), "start": "11:00", "length": "60", "capacity": "8"}
    )
    assert OFFICE_NAMES.findall(page.text) == ["London ", "Manchester"]
    assert FREE_ROOMS.findall(page.text) == ["Board", "Den"]  # free back to back; 8+ seats


@pytest.mark.parametrize(
    ("params", "message"),
    [
        ({"date": uk_day(-1), "start": "10:00", "length": "30"}, service.IN_THE_PAST),
        ({"date": uk_day(1), "start": "10:00", "length": "30", "capacity": "a"}, "whole number"),
        ({"date": "2027-03-28", "start": "01:30", "length": "30"}, "clocks go forward"),
    ],
    ids=["past", "bad capacity", "time the clocks skip"],
)
def test_search_refusals_show_the_reason(client, act, ids, params, message):
    act("hannah")
    page = client.get("/rooms", params=params)
    assert page.status_code == 422
    assert message in page.text
    assert 'class="free-room"' not in page.text


def test_book_with_attendees_and_details_for_everyone(client, act, room, book, ids, table, caplog):
    snug = room("Snug")
    caplog.set_level(logging.INFO, logger="roombooker.bookings")
    response = book(
        "hannah", snug, day=uk_day(89), start="14:00", length="75", title="  Sprint   review ",
        attendees=[ids["ben"], ids["kieran"], ids["hannah"], ids["ben"]],
    )
    new_id = booking_id(response)
    assert f"bookings: person_id={ids['hannah']} book booking_id={new_id}" in caplog.text
    assert table("SELECT title FROM bookings") == [("Sprint review",)]
    assert sorted(table("SELECT person_id FROM booking_attendees")) == sorted(
        [(ids["ben"],), (ids["kieran"],)]  # no repeats, and not the organiser
    )

    page = client.get(response.headers["location"])
    assert ANNOUNCE.search(page.text)[1] == '<p class="notice">Booked. Snug, 14:00–15:15.</p>'
    assert "Snug, London" in page.text and "Hannah Okafor" in page.text
    assert ">Cancel booking</a>" in page.text

    act("joanne")  # anyone sees room, time, title and organiser
    page = client.get(f"/bookings/{new_id}?notice=booked")
    assert ANNOUNCE.search(page.text)[1] == ""
    assert "Sprint review" in page.text and "Hannah Okafor" in page.text and "15:15" in page.text
    assert "Cancel booking" not in page.text


@pytest.mark.parametrize(
    ("viewer", "sees"),
    [("hannah", True), ("ben", True), ("anna", True), ("kieran", False), ("joanne", False)],
    ids=["organiser", "attendee", "room's office manager", "someone else", "other manager"],
)
def test_attendees_shown_only_to_organiser_attendees_and_room_managers(
    client, act, room, book, ids, viewer, sees
):
    new_id = booking_id(book("hannah", room("Snug"), attendees=[ids["ben"]]))
    act(viewer)
    page = client.get(f"/bookings/{new_id}")
    assert ("Attendees" in page.text) is sees
    assert ("Ben Adeyemi" in page.text) is sees


@pytest.mark.parametrize(
    ("change", "status", "message"),
    [
        ({"start": "10:45", "length": "30"}, 409, "Someone has already booked Snug at that time."),
        ({"day": uk_day(-1)}, 422, service.IN_THE_PAST),
        ({"day": uk_day(91)}, 422, service.TOO_FAR_AHEAD),
        ({"start": "10:10"}, 422, service.NOT_ON_QUARTER),
        ({"length": "255"}, 422, service.BAD_LENGTH),
        ({"length": "0"}, 422, service.BAD_LENGTH),
        ({"title": "   "}, 422, service.NEEDS_TITLE),
        ({"room": "closed"}, 409, "Attic is closed. Pick another room."),
    ],
    ids=["overlap", "past", "over 90 days", "off the quarter", "over 4 h", "zero", "no title",
         "closed room"],
)
def test_refused_bookings_keep_the_form(room, book, ids, table, change, status, message):
    snug = room("Snug")
    attic = room("Attic", closed=True)
    booking_id(book("anna", snug, start="10:00", length="60"))  # 10:00-11:00

    room_id = attic if change.pop("room", None) else snug
    title = change.pop("title", "Kick-off")
    response = book("hannah", room_id, title=title, attendees=[ids["ben"]], **change)

    assert response.status_code == status
    assert message in ANNOUNCE.search(response.text)[1]
    assert f'value="{title}"' in response.text  # what was typed stays
    assert f'name="attendee_id" value="{ids["ben"]}"' in response.text
    assert len(table("SELECT id FROM bookings")) == 1


def test_two_people_booking_the_same_slot_at_once(room, ids, table):
    snug = room("Snug")
    start = uk.uk_to_utc(date.fromisoformat(uk_day(2)), time(9, 0))
    barrier = threading.Barrier(2)
    outcomes: list[str] = []

    def attempt(who: str) -> None:
        with Session(db.get_engine(), expire_on_commit=False) as session:
            person = people_service.get_active_person(session, ids[who])
            barrier.wait()
            try:
                service.book(session, person, snug, start, 60, who, [])
                outcomes.append("booked")
            except service.BookingConflict:
                outcomes.append("conflict")

    threads = [threading.Thread(target=attempt, args=(who,)) for who in ("ben", "hannah")]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert sorted(outcomes) == ["booked", "conflict"]
    assert len(table("SELECT id FROM bookings")) == 1


def test_database_refuses_overlaps_and_closed_rooms(room, ids, db_path):
    snug = room("Snug")
    attic = room("Attic", closed=True)
    insert = "INSERT INTO bookings (room_id, organiser_id, title, start_at, end_at) VALUES (?,?,?,?,?)"
    with sqlite3.connect(db_path) as conn:
        conn.execute(insert, (snug, ids["ben"], "a", "2030-01-01T10:00:00Z", "2030-01-01T11:00:00Z"))
        conn.execute(insert, (snug, ids["ben"], "b", "2030-01-01T11:00:00Z", "2030-01-01T12:00:00Z"))
        with pytest.raises(sqlite3.IntegrityError, match="booking_conflict"):
            conn.execute(insert, (snug, ids["ben"], "c", "2030-01-01T10:30:00Z", "2030-01-01T10:45:00Z"))
        with pytest.raises(sqlite3.IntegrityError, match="booking_conflict"):
            conn.execute("UPDATE bookings SET start_at = '2030-01-01T10:45:00Z' WHERE title = 'b'")
        with pytest.raises(sqlite3.IntegrityError, match="room_closed"):
            conn.execute(insert, (attic, ids["ben"], "d", "2030-01-01T10:00:00Z", "2030-01-01T11:00:00Z"))


def test_only_the_organiser_cancels(client, act, room, book, ids, table):
    snug = room("Snug")
    new_id = booking_id(book("hannah", snug, attendees=[ids["ben"]]))

    act("anna")  # not even the room's office manager
    assert client.get(f"/bookings/{new_id}/cancel").status_code == 403
    refused = client.post(f"/bookings/{new_id}/cancel")
    assert refused.status_code == 403 and service.ONLY_ORGANISER in refused.text
    assert len(table("SELECT id FROM bookings")) == 1

    act("hannah")
    confirm = client.get(f"/bookings/{new_id}/cancel")
    assert "Cancel this booking?" in confirm.text and ">Keep booking</a>" in confirm.text
    response = client.post(f"/bookings/{new_id}/cancel")
    assert response.status_code == 303 and response.headers["location"] == "/rooms?notice=cancelled"
    assert table("SELECT id FROM bookings") == [] and table("SELECT * FROM booking_attendees") == []
    assert client.get(f"/bookings/{new_id}").status_code == 404
    booking_id(book("ben", snug))  # the slot is free again


def test_closing_a_room_cancels_its_future_bookings(client, act, room, book, ids, table, db_path):
    snug = room("Snug")
    future = booking_id(book("hannah", snug, attendees=[ids["ben"]]))
    with sqlite3.connect(db_path) as conn:  # bookings can't be made in the past, so write one
        conn.execute(
            "INSERT INTO bookings (room_id, organiser_id, title, start_at, end_at) "
            "VALUES (?, ?, 'Last week', '2020-01-01T10:00:00Z', '2020-01-01T11:00:00Z')",
            (snug, ids["hannah"]),
        )

    act("anna")
    assert client.post(f"/manage-rooms/{snug}/close").status_code == 303

    assert table("SELECT title FROM bookings") == [("Last week",)]
    assert table("SELECT * FROM booking_attendees") == []
    assert client.get(f"/bookings/{future}").status_code == 404


def test_uk_time_conversion():
    summer = uk.uk_to_utc(date(2027, 7, 1), time(9, 0))
    assert uk.to_text(summer) == "2027-07-01T08:00:00Z"
    assert (uk.clock(summer), uk.day(summer)) == ("09:00", "Thu 1 Jul")
    winter = uk.uk_to_utc(date(2027, 1, 5), time(9, 0))
    assert uk.to_text(winter) == "2027-01-05T09:00:00Z"
    assert uk.uk_to_utc(date(2027, 3, 28), time(1, 30)) is None  # the clocks skip it
    assert uk.utc_to_uk(summer) == (date(2027, 7, 1), "09:00")


# Book again ----------------------------------------------------------------------------

BOOK_AGAIN = re.compile(r'<a class="button button-secondary" href="(/bookings/new\?[^"]*)">Book again</a>')
PICKERS = 'id="booking-date"'


def book_again_url(page) -> str:
    """The Book again link's URL on a details page (HTML-unescaped)."""
    return BOOK_AGAIN.search(page.text)[1].replace("&amp;", "&")


def hidden(name: str, value) -> str:
    return f'<input type="hidden" name="{name}" value="{value}">'


def chosen(person_id: int) -> str:
    return f'name="attendee_id" value="{person_id}"'


@pytest.fixture
def insert_booking(db_path):
    """Write a booking straight to the file, for times the web refuses (past, far ahead)."""

    def _insert(room_id: int, organiser_id: int, start_at: str, end_at: str, title="Old") -> int:
        with sqlite3.connect(db_path) as conn:
            return conn.execute(
                "INSERT INTO bookings (room_id, organiser_id, title, start_at, end_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (room_id, organiser_id, title, start_at, end_at),
            ).lastrowid

    return _insert


def test_book_again_link_only_for_the_organiser(client, act, room, book, ids, insert_booking):
    snug = room("Snug")
    new_id = booking_id(book("hannah", snug, attendees=[ids["ben"]]))
    ended = insert_booking(snug, ids["hannah"], "2020-01-07T10:00:00Z", "2020-01-07T11:00:00Z")

    act("hannah")
    assert BOOK_AGAIN.search(client.get(f"/bookings/{new_id}").text)
    assert BOOK_AGAIN.search(client.get(f"/bookings/{ended}").text)  # ended ones too
    assert not BOOK_AGAIN.search(client.get(f"/bookings/{new_id}/cancel").text)
    for viewer in ("ben", "anna", "kieran"):  # attendee, room's manager, someone else
        act(viewer)
        assert not BOOK_AGAIN.search(client.get(f"/bookings/{new_id}").text)


def test_book_again_free_next_week(client, act, room, book, ids, table):
    snug = room("Snug")
    attendees = [ids["ben"], ids["kieran"]]
    first = booking_id(book("hannah", snug, title="Stand-up", attendees=attendees))
    form = client.get(book_again_url(client.get(f"/bookings/{first}")))

    assert form.status_code == 200
    assert ANNOUNCE.search(form.text)[1] == ""
    assert PICKERS not in form.text
    assert hidden("room", snug) in form.text and hidden("date", uk_day(8)) in form.text
    assert hidden("start", "10:00") in form.text and hidden("length", 60) in form.text
    assert 'value="Stand-up"' in form.text
    assert all(chosen(a) in form.text for a in attendees)

    second = booking_id(
        book("hannah", snug, day=uk_day(8), title="Stand-up", attendees=attendees)
    )
    week_later = uk.to_text(uk.uk_to_utc(date.fromisoformat(uk_day(8)), time(10, 0)))
    assert table("SELECT start_at, title FROM bookings WHERE id = ?", second) == [
        (week_later, "Stand-up")
    ]
    original = uk.to_text(uk.uk_to_utc(date.fromisoformat(uk_day(1)), time(10, 0)))
    assert table("SELECT start_at FROM bookings WHERE id = ?", first) == [(original,)]
    for booking in (first, second):
        assert len(table("SELECT * FROM booking_attendees WHERE booking_id = ?", booking)) == 2


def test_book_again_slot_taken_shows_pickers_then_check_time(client, act, room, book, ids):
    snug = room("Snug")
    first = booking_id(book("hannah", snug, title="Stand-up", attendees=[ids["ben"]]))
    booking_id(book("anna", snug, day=uk_day(8), start="10:00", length="30"))

    act("hannah")
    form = client.get(book_again_url(client.get(f"/bookings/{first}")))
    assert form.status_code == 200  # htmx swaps only 2xx
    assert ANNOUNCE.search(form.text)[1] == (
        '<p class="error-message" role="alert">'
        "Someone has already booked Snug at that time. Pick another time.</p>"
    )
    assert PICKERS in form.text and ">Check time</button>" in form.text
    assert '<option value="10:00" selected>' in form.text
    assert '<option value="60" selected>' in form.text
    assert 'value="Stand-up"' in form.text and chosen(ids["ben"]) in form.text

    checked = client.get(
        "/bookings/new",
        params={"room": snug, "date": uk_day(8), "start": "11:00", "length": "60",
                "title": "Stand-up", "attendee_id": ids["ben"]},
    )
    assert checked.status_code == 200
    assert ANNOUNCE.search(checked.text)[1] == ""
    assert PICKERS not in checked.text
    assert 'value="Stand-up"' in checked.text and chosen(ids["ben"]) in checked.text
    booking_id(book("hannah", snug, day=uk_day(8), start="11:00", attendees=[ids["ben"]]))


def test_refused_title_on_a_taken_slot_announces_both(room, book, ids, table):
    snug = room("Snug")
    booking_id(book("anna", snug, start="10:00", length="60"))
    response = book("hannah", snug, title="   ", attendees=[ids["ben"]])
    assert response.status_code == 422
    announced = ANNOUNCE.search(response.text)[1]
    assert service.NEEDS_TITLE in announced
    assert "Someone has already booked Snug at that time." in announced
    assert PICKERS in response.text and chosen(ids["ben"]) in response.text
    assert len(table("SELECT id FROM bookings")) == 1


def test_book_again_keeps_the_uk_clock_time_across_a_clock_change(
    client, act, room, ids, insert_booking
):
    snug = room("Snug")
    # Sun 21 Mar 2027 09:00 GMT; the clocks go forward on 28 Mar.
    old = insert_booking(snug, ids["hannah"], "2027-03-21T09:00:00Z", "2027-03-21T10:00:00Z")
    act("hannah")
    url = book_again_url(client.get(f"/bookings/{old}"))
    assert "date=2027-03-28&start=09%3A00&length=60" in url
    assert uk.to_text(uk.uk_to_utc(date(2027, 3, 28), time(9, 0))) == "2027-03-28T08:00:00Z"


@pytest.mark.parametrize(
    ("start_at", "end_at", "message"),
    [
        ("2020-01-07T10:00:00Z", "2020-01-07T11:00:00Z", service.IN_THE_PAST),
        (None, None, service.TOO_FAR_AHEAD),
        ("2027-03-21T01:30:00Z", "2027-03-21T02:00:00Z", "clocks go forward"),
    ],
    ids=["still in the past", "over 90 days", "time the clocks skip"],
)
def test_book_again_time_no_longer_valid(
    client, act, room, ids, insert_booking, start_at, end_at, message
):
    snug = room("Snug")
    if start_at is None:  # 85 days ahead, so one week later is past the 90-day limit
        start = uk.uk_to_utc(date.fromisoformat(uk_day(85)), time(10, 0))
        start_at, end_at = uk.to_text(start), uk.to_text(start + timedelta(hours=1))
    old = insert_booking(snug, ids["hannah"], start_at, end_at, title="Retro")
    act("hannah")
    form = client.get(book_again_url(client.get(f"/bookings/{old}")))
    assert message in ANNOUNCE.search(form.text)[1]
    assert PICKERS in form.text and 'value="Retro"' in form.text


def test_book_again_room_closed(client, act, room, book, ids, table, insert_booking):
    attic = room("Attic")
    old = insert_booking(attic, ids["hannah"], "2020-01-07T10:00:00Z", "2020-01-07T11:00:00Z")
    act("anna")
    assert client.post(f"/manage-rooms/{attic}/close").status_code == 303

    act("hannah")
    form = client.get(book_again_url(client.get(f"/bookings/{old}")))
    assert "Attic is closed. Pick another room." in ANNOUNCE.search(form.text)[1]
    refused = book("hannah", attic, day=uk_day(8))
    assert refused.status_code == 409 and "Attic is closed." in refused.text
    assert len(table("SELECT id FROM bookings")) == 1


def test_book_again_drops_an_attendee_who_left(client, act, room, book, ids, load_csv):
    snug = room("Snug")
    first = booking_id(book("hannah", snug, attendees=[ids["ben"], ids["kieran"]]))
    assert load_csv(*(line for line in PEOPLE if not line.startswith("ben@"))) == 0

    act("hannah")
    form = client.get(book_again_url(client.get(f"/bookings/{first}")))
    assert chosen(ids["kieran"]) in form.text
    assert chosen(ids["ben"]) not in form.text and "Ben Adeyemi" not in form.text


def test_normal_booking_form_has_no_pickers(client, act, room):
    snug = room("Snug")
    act("hannah")
    form = client.get(
        "/bookings/new", params={"room": snug, "date": uk_day(1), "start": "10:00", "length": "30"}
    )
    assert form.status_code == 200
    assert ANNOUNCE.search(form.text)[1] == ""
    assert PICKERS not in form.text and "Check time" not in form.text
    assert hidden("date", uk_day(1)) in form.text
