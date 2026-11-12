"""Seed `--demo-bookings`: demo rooms and bookings for this week and next."""

import logging
import sqlite3
from datetime import timedelta
from pathlib import Path

from roombooker import seed
from roombooker.core import time as clock

BUILD_SEED = Path(__file__).resolve().parent.parent / "seeds" / "build-people.csv"


def _bookings(db_path):
    """Every booking as (office, uk_date, organiser_email, attendee emails)."""
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            "SELECT b.id, o.name, b.start_at, p.email FROM bookings b "
            "JOIN rooms r ON r.id = b.room_id JOIN offices o ON o.id = r.office_id "
            "JOIN people p ON p.id = b.organiser_id"
        ).fetchall()
        attendees = conn.execute(
            "SELECT a.booking_id, p.email FROM booking_attendees a JOIN people p ON p.id = a.person_id"
        ).fetchall()
    by_booking: dict[int, set[str]] = {}
    for booking_id, email in attendees:
        by_booking.setdefault(booking_id, set()).add(email)
    return [
        (office, clock.from_text(start).astimezone(clock.UK).date(), email, by_booking.get(i, set()))
        for i, office, start, email in rows
    ]


def _count(db_path, table):
    with sqlite3.connect(db_path) as conn:
        return conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0]


def test_demo_bookings_fill_this_week_and_next_in_every_office(db_path):
    assert seed.main([str(BUILD_SEED)]) == 0
    assert _count(db_path, "bookings") == 0  # nothing without the flag

    assert seed.main([str(BUILD_SEED), "--demo-bookings"]) == 0

    seeded = {line.split(",")[0] for line in BUILD_SEED.read_text().splitlines()[1:]}
    monday = clock.week_start(clock.uk_now().date())
    rows = _bookings(db_path)
    assert {office for office, *_ in rows} == {"London", "Manchester", "Leeds"}
    days = {day for _, day, *_ in rows}
    assert days == {monday + timedelta(days=d) for d in (*range(5), *range(7, 12))}
    assert all(organiser in seeded and attendees <= seeded for _, _, organiser, attendees in rows)
    assert all(attendees for *_, attendees in rows)


def test_rerun_adds_no_rooms_or_bookings(db_path, caplog):
    assert seed.main([str(BUILD_SEED), "--demo-bookings"]) == 0
    rooms, bookings = _count(db_path, "rooms"), _count(db_path, "bookings")
    caplog.set_level(logging.INFO, logger="roombooker.seed")

    assert seed.main([str(BUILD_SEED), "--demo-bookings"]) == 0

    assert (_count(db_path, "rooms"), _count(db_path, "bookings")) == (rooms, bookings)
    assert f"demo rooms 0 added, {rooms} already there" in caplog.text
    assert f"demo bookings 0 added, {bookings} skipped" in caplog.text


def test_without_the_build_seed_nothing_demo_is_written(db_path, capsys):
    path = db_path.parent / "hr.csv"
    path.write_text(
        "email,name,office,office_manager\nanna.kowalski@example.com,Anna Kowalski,London,true\n"
    )

    assert seed.main([str(path), "--demo-bookings"]) == 1

    assert "error: demo bookings need the build seed: " in capsys.readouterr().err
    assert (_count(db_path, "rooms"), _count(db_path, "bookings")) == (0, 0)
