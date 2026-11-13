"""Bookings as a standard iCalendar (RFC 5545) text. Pure: no database, no clock.

Imported only by `bookings.service`. Times are written in UTC (`...Z`) from the
booking's stored moments, so calendar apps show the right UK time on both sides of a
clock change without a VTIMEZONE block. No ATTENDEE or ORGANIZER lines: an import is
never an invitation, and no attendee names or emails go into the file.

The same formatter writes Add to calendar's one-event download and each person's
subscribed feed (a named calendar with a refresh hint).
"""

import hashlib
from collections.abc import Iterable
from datetime import datetime
from typing import TYPE_CHECKING

from roombooker.core import time as clock

if TYPE_CHECKING:
    from roombooker.bookings.service import BookingView

PRODID = "-//Room booker//EN"
LINE_OCTETS = 75
CRLF = "\r\n"
REFRESH = "PT1H"


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


def uid(booking: "BookingView") -> str:
    """`booking-<id>-<hash>@roombooker`. The hash covers the room, times and title, so a
    booking id SQLite reuses after a delete is a new event, never an update of the old."""
    content = "\n".join(
        [
            str(booking.room.id),
            clock.to_text(booking.start_at),
            clock.to_text(booking.end_at),
            booking.title,
        ]
    )
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()[:8]
    return f"booking-{booking.id}-{digest}@roombooker"


def _event(booking: "BookingView", stamp: datetime) -> list[str]:
    return [
        "BEGIN:VEVENT",
        f"UID:{uid(booking)}",
        f"DTSTAMP:{clock.ical_utc(stamp)}",
        f"DTSTART:{clock.ical_utc(booking.start_at)}",
        f"DTEND:{clock.ical_utc(booking.end_at)}",
        f"SUMMARY:{escape(booking.title)}",
        f"LOCATION:{escape(f'{booking.room.name}, {booking.office_name}')}",
        f"DESCRIPTION:{escape(f'Booked by {booking.organiser_name}')}",
        "STATUS:CONFIRMED",
        "END:VEVENT",
    ]


def calendar(events: Iterable["BookingView"], stamp: datetime, name: str | None = None) -> str:
    """A VCALENDAR holding one VEVENT per booking, CRLF line endings, folded lines.

    With a `name` (a subscribed feed) it also names the calendar and asks apps to refresh
    hourly; without one the calendar lines are the download's."""
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        f"PRODID:{PRODID}",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
    ]
    if name is not None:
        lines += [
            f"X-WR-CALNAME:{escape(name)}",
            f"REFRESH-INTERVAL;VALUE=DURATION:{REFRESH}",
            f"X-PUBLISHED-TTL:{REFRESH}",
        ]
    for booking in events:
        lines.extend(_event(booking, stamp))
    lines.append("END:VCALENDAR")
    return "".join(fold(line) + CRLF for line in lines)
