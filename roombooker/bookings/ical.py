"""Bookings as a standard iCalendar (RFC 5545) text. Pure: no database, no clock.

Imported only by `bookings.service`. Times are written in UTC (`...Z`) from the
booking's stored moments, so calendar apps show the right UK time on both sides of a
clock change without a VTIMEZONE block. No ATTENDEE or ORGANIZER lines: an import is
never an invitation, and no attendee names or emails go into the file.
"""

from collections.abc import Iterable
from datetime import datetime
from typing import TYPE_CHECKING

from roombooker.core import time as clock

if TYPE_CHECKING:
    from roombooker.bookings.service import BookingView

PRODID = "-//Room booker//EN"
LINE_OCTETS = 75
CRLF = "\r\n"


def escape(text: str) -> str:
    """TEXT value escaping: backslash, semicolon, comma and line breaks."""
    text = text.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,")
    text = text.replace("\r\n", "\\n").replace("\r", "\\n").replace("\n", "\\n")
    # RFC 5545 TEXT allows no control characters except HTAB.
    return "".join(ch for ch in text if ch == "\t" or not (ch < " " or ch == "\x7f"))


def fold(line: str) -> str:
    """Split a content line into physical lines of at most 75 octets, each continuation
    starting with a space, never inside a UTF-8 character."""
    parts: list[str] = []
    current, size, limit = [], 0, LINE_OCTETS
    for char in line:
        octets = len(char.encode("utf-8"))
        if size + octets > limit:
            parts.append("".join(current))
            current, size, limit = [], 0, LINE_OCTETS - 1  # the leading space counts
        current.append(char)
        size += octets
    parts.append("".join(current))
    return (CRLF + " ").join(parts)


def _event(booking: "BookingView", stamp: datetime) -> list[str]:
    return [
        "BEGIN:VEVENT",
        f"UID:booking-{booking.id}@roombooker",
        f"DTSTAMP:{clock.ical_utc(stamp)}",
        f"DTSTART:{clock.ical_utc(booking.start_at)}",
        f"DTEND:{clock.ical_utc(booking.end_at)}",
        f"SUMMARY:{escape(booking.title)}",
        f"LOCATION:{escape(f'{booking.room.name}, {booking.office_name}')}",
        f"DESCRIPTION:{escape(f'Booked by {booking.organiser_name}')}",
        "STATUS:CONFIRMED",
        "END:VEVENT",
    ]


def calendar(events: Iterable["BookingView"], stamp: datetime) -> str:
    """A VCALENDAR holding one VEVENT per booking, CRLF line endings, folded lines."""
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        f"PRODID:{PRODID}",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
    ]
    for booking in events:
        lines.extend(_event(booking, stamp))
    lines.append("END:VCALENDAR")
    return "".join(fold(line) + CRLF for line in lines)
