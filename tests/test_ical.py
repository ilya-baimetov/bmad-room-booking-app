"""The iCalendar formatter, without a database: escaping, folding, CRLF and UTC times."""

from datetime import UTC, date, datetime, time

from roombooker.bookings import ical
from roombooker.bookings.service import BookingView
from roombooker.core import time as uk
from roombooker.rooms.service import Room

STAMP = datetime(2026, 11, 13, 8, 30, tzinfo=UTC)


def view(**changes) -> BookingView:
    fields = {
        "id": 7,
        "room": Room(id=1, office_id=1, name="Snug", capacity=4, is_closed=False),
        "office_name": "London",
        "start_at": datetime(2026, 11, 24, 10, 0, tzinfo=UTC),
        "end_at": datetime(2026, 11, 24, 11, 0, tzinfo=UTC),
        "title": "Planning",
        "organiser_id": 3,
        "organiser_name": "Hannah Okafor",
        "attendees_visible": True,
        "attendees": ("Ben Adeyemi",),
        "can_cancel": True,
        "attendee_ids": (2,),
    }
    return BookingView(**(fields | changes))


def unfold(text: str) -> list[str]:
    return text.replace("\r\n ", "").split("\r\n")


def test_one_event_with_utc_times_and_no_attendees():
    text = ical.calendar([view()], STAMP)
    assert text.endswith("\r\n") and "\n" not in text.replace("\r\n", "")
    assert unfold(text) == [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Room booker//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "BEGIN:VEVENT",
        "UID:booking-7@roombooker",
        "DTSTAMP:20261113T083000Z",
        "DTSTART:20261124T100000Z",
        "DTEND:20261124T110000Z",
        "SUMMARY:Planning",
        "LOCATION:Snug\\, London",
        "DESCRIPTION:Booked by Hannah Okafor",
        "STATUS:CONFIRMED",
        "END:VEVENT",
        "END:VCALENDAR",
        "",
    ]
    assert "Ben Adeyemi" not in text and "ATTENDEE" not in text and "ORGANIZER" not in text
    assert "VTIMEZONE" not in text


def test_ical_utc_converts_aware_times_to_utc():
    summer = uk.uk_to_utc(date(2027, 7, 6), time(10, 0))
    assert uk.ical_utc(summer) == "20270706T090000Z"
    assert uk.ical_utc(summer.astimezone(uk.UK)) == "20270706T090000Z"


def test_text_is_escaped():
    assert ical.escape("a\\b;c,d\ne\r\nf") == "a\\\\b\\;c\\,d\\ne\\nf"
    assert ical.escape("a\x00b\x08c\x0b\x0c\x0ed\x1fe\x7ff\tg") == "abcdef\tg"
    text = ical.calendar([view(title="Q1; budget, plans \\ más")], STAMP)
    assert "SUMMARY:Q1\\; budget\\, plans \\\\ más" in unfold(text)


def test_long_lines_fold_at_75_octets_without_splitting_a_character():
    title = "Ünïcödé review — " + "é" * 90  # ~100 characters, mostly two octets each
    text = ical.calendar([view(title=title, organiser_name="Siobhán Ó Briain")], STAMP)
    physical = text.split("\r\n")
    assert all(len(line.encode("utf-8")) <= 75 for line in physical)
    assert any(line.startswith(" ") for line in physical)
    assert f"SUMMARY:{title}" in unfold(text)
    assert "DESCRIPTION:Booked by Siobhán Ó Briain" in unfold(text)


def test_fold_at_a_multibyte_boundary():
    line = "X" * 74 + "€" + "Y"  # the 3-octet € would straddle octet 75
    folded = ical.fold(line)
    first, second = folded.split("\r\n")
    assert first == "X" * 74 and second == " €Y"
    assert ical.fold("X" * 75) == "X" * 75
    assert ical.fold("X" * 76) == "X" * 75 + "\r\n X"
