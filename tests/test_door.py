"""Door tablets and check-in: setting up, replacing and removing a room's tablet on
Manage rooms, the door page, and one-tap check-in inside its window.

The clock is fixed by patching `core.time.utc_now`. 17 Nov 2026 is in GMT, so UK
times equal UTC times in these tests.
"""

import logging
import re
import sqlite3
from datetime import UTC, datetime, timedelta

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy.orm import Session

from roombooker.bookings import service
from roombooker.core import db
from roombooker.core import time as uk
from tests.conftest import ROOT

PEOPLE = (
    "anna@example.com,Anna Kowalski,London,true",
    "ben@example.com,Ben Adeyemi,London,",
    "joanne@example.com,Joanne Price,Manchester,true",
)
DAY = datetime(2026, 11, 17, tzinfo=UTC)
START = DAY.replace(hour=10)  # the booking under test: 10:00–11:00
SET_UP = DAY.replace(hour=8)
NOT_SET_UP = "This tablet isn't set up for a room. Ask your office manager to set it up."
CHECK_IN_BUTTON = re.compile(r'<form method="post" action="/door/check-in/(\d+)">')
ANNOUNCE = re.compile(r'<div id="announce"[^>]*>(.*?)</div>', re.DOTALL)


def at(minutes: int, base: datetime = START) -> datetime:
    return base + timedelta(minutes=minutes)


@pytest.fixture
def clock(monkeypatch):
    """Set the app's clock: `clock(moment)`. Starts at 08:00 on DAY."""
    now = {"moment": SET_UP}
    monkeypatch.setattr(uk, "utc_now", lambda: now["moment"])

    def _set(moment: datetime) -> None:
        now["moment"] = moment

    return _set


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
    def _room(name: str, manager: str = "anna") -> int:
        act(manager)
        assert client.post("/manage-rooms", data={"name": name, "capacity": "6"}).status_code == 303
        with sqlite3.connect(db_path) as conn:
            return conn.execute("SELECT id FROM rooms WHERE name = ?", (name,)).fetchone()[0]

    return _room


@pytest.fixture
def insert_booking(db_path, ids):
    def _insert(room_id: int, start: datetime, minutes: int = 60, title: str = "Planning") -> int:
        with sqlite3.connect(db_path) as conn:
            return conn.execute(
                "INSERT INTO bookings (room_id, organiser_id, title, start_at, end_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    room_id,
                    ids["ben"],
                    title,
                    uk.to_text(start),
                    uk.to_text(start + timedelta(minutes=minutes)),
                ),
            ).lastrowid

    return _insert


@pytest.fixture
def tablets(db_path):
    def _tablets(room_id: int) -> list[dict]:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM room_tablets WHERE room_id = ? ORDER BY id", (room_id,)
            ).fetchall()
        return [dict(row) for row in rows]

    return _tablets


@pytest.fixture
def set_up(client, act):
    """Set up the room's tablet as `manager`; returns the new tablet's token. The client
    is then that tablet (door_tablet cookie, no person cookie)."""

    def _set_up(room_id: int, manager: str = "anna") -> str:
        act(manager)
        response = client.post(f"/manage-rooms/{room_id}/tablet")
        assert response.status_code == 303
        assert response.headers["location"] == "/door"
        return client.cookies["door_tablet"]

    return _set_up


def checked_in_at(db_path, booking_id: int) -> str | None:
    with sqlite3.connect(db_path) as conn:
        return conn.execute(
            "SELECT checked_in_at FROM bookings WHERE id = ?", (booking_id,)
        ).fetchone()[0]


def as_tablet(client, token: str | None) -> None:
    client.cookies.clear()
    if token is not None:
        client.cookies.set("door_tablet", token)


# Setting up, replacing, removing -----------------------------------------------------


def test_set_up_confirms_in_the_row_then_lands_on_the_door(
    client, act, room, set_up, insert_booking, tablets, clock, caplog
):
    snug = room("Snug")
    insert_booking(snug, START)

    act("anna")
    page = client.get(f"/manage-rooms/{snug}/tablet")
    assert "<html" in page.text
    assert "Set up this browser as the door tablet for Snug?" in page.text
    assert "you will be signed out in this browser" in page.text
    assert (
        "Mount it with the screen centre about 120 cm from the floor "
        "and set it never to sleep."
    ) in page.text
    row = client.get(f"/manage-rooms/{snug}/tablet", headers={"HX-Request": "true"})
    assert row.text.startswith(f'<tr id="room-{snug}" class="room-row is-confirming">')
    assert 'hx-post' not in row.text  # a plain form: the browser must follow the redirect
    assert tablets(snug) == []  # asking changes nothing

    with caplog.at_level(logging.INFO, logger="roombooker"):
        response = client.post(f"/manage-rooms/{snug}/tablet")
    assert response.status_code == 303 and response.headers["location"] == "/door"
    cookies = response.headers.get_list("set-cookie")
    assert any(c.startswith("door_tablet=") and "HttpOnly" in c for c in cookies)
    assert any(c.startswith("person_id=") and "Max-Age=0" in c for c in cookies)
    token = client.cookies["door_tablet"]
    assert token not in caplog.text
    assert f"set up tablet_id={tablets(snug)[0]['id']} room_id={snug}" in caplog.text

    door = client.get("/door")
    assert door.status_code == 200
    assert "<title>Snug · Room Booking</title>" in door.text
    assert "10:00–11:00" in door.text and "Planning" in door.text

    act("anna")  # the manager's main window
    assert "Since 17 Nov" in client.get("/manage-rooms").text
    assert tablets(snug)[0]["set_up_at"] == "2026-11-17T08:00:00Z"
    assert tablets(snug)[0]["removed_at"] is None


def test_only_the_office_manager_sets_up_or_removes(client, act, room, set_up, tablets, clock):
    snug = room("Snug")
    for who in ("ben", "joanne"):  # not a manager; another office's manager
        act(who)
        assert client.get(f"/manage-rooms/{snug}/tablet").status_code == 403
        assert client.post(f"/manage-rooms/{snug}/tablet").status_code == 403
        assert "door_tablet" not in client.cookies
    set_up(snug)
    for who in ("ben", "joanne"):
        act(who)
        assert client.post(f"/manage-rooms/{snug}/tablet/remove").status_code == 403
    assert [t["removed_at"] for t in tablets(snug)] == [None]


def test_set_up_again_replaces_the_old_tablet(client, room, set_up, tablets, clock):
    snug = room("Snug")
    old = set_up(snug)
    clock(at(30, SET_UP))
    new = set_up(snug)

    assert old != new
    first, second = tablets(snug)
    assert first["removed_at"] == second["set_up_at"] == "2026-11-17T08:30:00Z"
    assert second["removed_at"] is None
    as_tablet(client, old)
    assert NOT_SET_UP in client.get("/door").text
    as_tablet(client, new)
    assert "<h1 class=\"title\">Snug</h1>" in client.get("/door").text


def test_remove_confirms_in_the_row_from_any_browser(client, act, room, set_up, tablets, clock):
    snug = room("Snug")
    token = set_up(snug)

    act("anna")  # another browser: the manager's own
    page = client.get("/manage-rooms")
    assert "Remove tablet" in page.text
    confirm = client.get(f"/manage-rooms/{snug}/tablet/remove")
    assert "Remove the door tablet from Snug?" in confirm.text
    assert tablets(snug)[0]["removed_at"] is None

    clock(at(5, SET_UP))
    row = client.post(f"/manage-rooms/{snug}/tablet/remove", headers={"HX-Request": "true"})
    assert row.status_code == 200
    assert '<td class="room-tablet">No door tablet</td>' in row.text
    assert "Remove tablet" not in row.text
    assert '<p class="notice">Removed the door tablet from Snug.</p>' in row.text
    assert tablets(snug)[0]["removed_at"] == "2026-11-17T08:05:00Z"

    again = client.post(f"/manage-rooms/{snug}/tablet/remove")  # nothing left: no change
    assert again.status_code == 303
    assert again.headers["location"] == f"/manage-rooms?notice=tablet_removed&room={snug}"
    assert len(tablets(snug)) == 1

    as_tablet(client, token)
    assert NOT_SET_UP in client.get("/door").text


@pytest.mark.parametrize("token", [None, "", "nonsense", "x" * 500])
def test_door_without_a_valid_tablet_shows_not_set_up(client, db_path, token):
    as_tablet(client, token)
    page = client.get("/door")
    assert page.status_code == 200
    assert NOT_SET_UP in page.text
    assert client.post("/door/check-in/1").status_code == 403


# The door page -----------------------------------------------------------------------


def test_door_page_has_no_links_and_no_top_bar(client, room, set_up, insert_booking, clock):
    snug = room("Snug")
    insert_booking(snug, START)
    set_up(snug)
    clock(at(0))
    for page in (client.get("/door"), client.post("/door/check-in/999999")):
        assert '<html lang="en-GB">' in page.text
        assert "<a " not in page.text
        assert "top-bar" not in page.text and "app-name" not in page.text


def test_door_lists_only_todays_bookings_and_marks_current_or_next(
    client, room, set_up, insert_booking, clock
):
    snug, den = room("Snug"), room("Den")
    early = insert_booking(snug, DAY.replace(hour=9), title="Early")
    late = insert_booking(snug, DAY.replace(hour=11), title="Late")
    insert_booking(snug, DAY - timedelta(hours=2), title="Yesterday")
    insert_booking(snug, DAY + timedelta(days=1, hours=9), title="Tomorrow")
    insert_booking(den, DAY.replace(hour=9), title="Other room")
    set_up(snug)

    clock(DAY.replace(hour=9, minute=30))
    page = client.get("/door").text
    assert "Early" in page and "Late" in page
    assert "Yesterday" not in page and "Tomorrow" not in page and "Other room" not in page
    assert page.index("Early") < page.index("Late")
    assert re.search(rf'id="booking-{early}" class="door-booking is-marked">\s*<strong class="door-marker">Now', page)

    clock(DAY.replace(hour=10, minute=30))
    page = client.get("/door").text
    assert re.search(rf'id="booking-{late}" class="door-booking is-marked">\s*<strong class="door-marker">Next', page)

    clock(DAY.replace(hour=13))
    assert "is-marked" not in client.get("/door").text


# Checking in -------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("minutes", "accepted", "refusal"),
    [
        (-6, False, "Check-in opens at 09:55."),
        (-5, True, None),
        (14, True, None),
        (15, False, "Check-in closed at 10:15."),
    ],
)
def test_check_in_only_inside_the_window(
    client, db_path, room, set_up, insert_booking, clock, minutes, accepted, refusal
):
    snug = room("Snug")
    booking = insert_booking(snug, START)
    set_up(snug)
    clock(at(minutes))

    page = client.get("/door")
    assert (CHECK_IN_BUTTON.findall(page.text) == [str(booking)]) is accepted
    response = client.post(f"/door/check-in/{booking}")
    if accepted:
        assert response.status_code == 303 and response.headers["location"] == "/door"
        assert checked_in_at(db_path, booking) == uk.to_text(at(minutes))
        page = client.get("/door")
        assert "✓ Checked in" in page.text
        assert CHECK_IN_BUTTON.findall(page.text) == []
    else:
        assert response.status_code == 422
        assert ANNOUNCE.search(response.text)[1] == f'<p class="error-message">{refusal}</p>'
        assert "Planning" in response.text  # the door page, re-rendered
        assert checked_in_at(db_path, booking) is None


def test_check_in_twice_keeps_the_first_time(
    client, db_path, room, set_up, insert_booking, clock, caplog
):
    snug = room("Snug")
    booking = insert_booking(snug, START)
    set_up(snug)
    clock(at(1))
    with caplog.at_level(logging.INFO, logger="roombooker"):
        assert client.post(f"/door/check-in/{booking}").status_code == 303
        clock(at(20))  # even after the window: it is already checked in
        assert client.post(f"/door/check-in/{booking}").status_code == 303
    assert checked_in_at(db_path, booking) == "2026-11-17T10:01:00Z"
    assert caplog.text.count(f"check in booking_id={booking}") == 1
    assert "✓ Checked in" in client.get("/door").text


def test_check_in_refuses_another_rooms_or_unknown_booking(
    client, db_path, room, set_up, insert_booking, clock
):
    snug, den = room("Snug"), room("Den")
    elsewhere = insert_booking(den, START)
    set_up(snug)
    clock(at(0))
    for booking_id in (elsewhere, 999999, 2**70):
        response = client.post(f"/door/check-in/{booking_id}")
        assert response.status_code == 404
        assert service.BookingNotFound.default_message in response.text
        assert "top-bar" not in response.text
    assert checked_in_at(db_path, elsewhere) is None


def test_booking_whose_window_no_tablet_covered_is_untracked(
    client, db_path, room, set_up, insert_booking, clock
):
    snug = room("Snug")
    booking = insert_booking(snug, START)
    clock(at(-2))  # set up after the window opened at 09:55
    set_up(snug)

    assert CHECK_IN_BUTTON.findall(client.get("/door").text) == []
    response = client.post(f"/door/check-in/{booking}")
    assert response.status_code == 422
    assert service.CHECK_IN_UNTRACKED.replace("'", "&#39;") in response.text
    assert checked_in_at(db_path, booking) is None


def test_booking_view_carries_the_check_in_state(
    client, db_path, ids, room, set_up, insert_booking, clock
):
    snug, den = room("Snug"), room("Den")
    tracked = insert_booking(snug, START)
    untracked = insert_booking(den, START)
    set_up(snug)
    clock(at(-10))

    def view(booking_id: int) -> service.BookingView:
        with Session(db.get_engine()) as session:
            person = service.people_service.get_active_person(session, ids["ben"])
            return service.get_booking(session, person, booking_id)

    before = view(tracked)
    assert (before.check_in, before.can_check_in) == ("awaiting", False)
    assert before.check_in_opens_at == at(-5)
    assert before.check_in_closes_at == at(15)
    assert before.freed_at is None
    clock(at(0))
    assert (view(tracked).check_in, view(tracked).can_check_in) == ("awaiting", True)
    assert (view(untracked).check_in, view(untracked).can_check_in) == ("untracked", False)
    client.post(f"/door/check-in/{tracked}")
    assert (view(tracked).check_in, view(tracked).can_check_in) == ("checked_in", False)


@pytest.mark.parametrize(
    ("periods", "covered"),
    [
        ([], False),
        ([(at(-5), None)], True),
        ([(at(-4), None)], False),  # set up after the window opened
        ([(at(-60), at(15))], True),
        ([(at(-60), at(14))], False),  # removed before the window closed
        ([(at(-60), at(0)), (at(0), None)], True),  # replaced: contiguous
        ([(at(0), None), (at(-60), at(0))], True),  # in any order
        ([(at(-60), at(0)), (at(1), None)], False),  # a gap
        ([(at(-60), at(-30))], False),
    ],
)
def test_coverage_of_the_check_in_window(periods, covered):
    assert service._covered(periods, START) is covered


# Migration ---------------------------------------------------------------------------


def test_migration_down_and_up_keeps_triggers_and_attendees(db_path, ids, room, insert_booking):
    snug = room("Snug")
    booking = insert_booking(snug, START)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "INSERT INTO booking_attendees (booking_id, person_id) VALUES (?, ?)",
            (booking, ids["anna"]),
        )
    db.get_engine().dispose()
    config = Config(str(ROOT / "alembic.ini"))
    config.attributes["configure_logger"] = False

    def state() -> tuple[set, list, list]:
        with sqlite3.connect(db_path) as conn:
            triggers = {
                row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'trigger'")
            }
            attendees = conn.execute("SELECT booking_id, person_id FROM booking_attendees").fetchall()
            columns = [row[1] for row in conn.execute("PRAGMA table_info(bookings)")]
        return triggers, attendees, columns

    triggers = {
        "bookings_no_overlap_insert",
        "bookings_no_overlap_update",
        "rooms_close_cancels_future_bookings",
    }
    command.downgrade(config, "0004")
    found, attendees, columns = state()
    assert found == triggers
    assert attendees == [(booking, ids["anna"])]
    assert "checked_in_at" not in columns and "freed_at" not in columns

    command.upgrade(config, "head")
    found, attendees, columns = state()
    assert found == triggers
    assert attendees == [(booking, ids["anna"])]
    assert columns[-2:] == ["checked_in_at", "freed_at"]
    with sqlite3.connect(db_path) as conn, pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "UPDATE bookings SET checked_in_at = 'a', freed_at = 'b' WHERE id = ?", (booking,)
        )
