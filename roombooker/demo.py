"""Demo rooms and bookings for a local run: `python -m roombooker.seed <csv> --demo-bookings`.

Bookings fall on the weekdays of this week and next (UK time), counted from the day the
command runs, so earlier days of this week are filled too. Everyone named here is in
`seeds/build-people.csv`. Rooms go through `rooms.service` and bookings through
`bookings.service` (AD-3), so the database triggers still refuse overlaps (AD-4).
A rerun keeps rooms that already exist and skips bookings whose slot is taken.
"""

import logging
from dataclasses import dataclass
from datetime import time, timedelta

from sqlalchemy.orm import Session

from roombooker.bookings import service as bookings_service
from roombooker.core import time as clock
from roombooker.people import service as people_service
from roombooker.people.service import Person
from roombooker.rooms import service as rooms_service
from roombooker.rooms.service import Room

log = logging.getLogger("roombooker.demo")

# Office -> the office manager who adds its rooms, and the rooms (name, capacity).
OFFICES: dict[str, tuple[str, tuple[tuple[str, int], ...]]] = {
    "London": (
        "anna.kowalski",
        (("Thames", 12), ("Fleet", 6), ("Kingsway", 4), ("Booth 1", 2)),
    ),
    "Manchester": ("joanne.price", (("Irwell", 10), ("Deansgate", 6), ("Ancoats", 4))),
    "Leeds": ("tariq.mahmood", (("Aire", 10), ("Briggate", 6), ("Kirkgate", 4))),
}


@dataclass(frozen=True)
class DemoBooking:
    week: int  # 0 this week, 1 next week
    weekday: int  # 0 Monday .. 4 Friday
    start: str  # UK clock time
    minutes: int
    office: str
    room: str
    title: str
    organiser: str  # email local part; every demo person is @example.com
    attendees: tuple[str, ...]


def _b(week, weekday, start, minutes, office, room, title, organiser, *attendees):
    return DemoBooking(week, weekday, start, minutes, office, room, title, organiser, attendees)


# Daily stand-ups in every office, both weeks.
_STANDUPS = tuple(
    _b(week, weekday, "09:30", 15, office, room, "Stand-up", organiser, *attendees)
    for week in (0, 1)
    for weekday in range(5)
    for office, room, organiser, attendees in (
        ("London", "Kingsway", "ben.adeyemi", ("chloe.fraser", "daniel.osei", "ella.marsh")),
        ("Manchester", "Ancoats", "kieran.walsh", ("laura.nkemelu", "mohammed.siddiqui", "niamh.gallagher")),
        ("Leeds", "Kirkgate", "ursula.finch", ("victor.ambrose", "wendy.carrick", "xavier.lund")),
    )
)

_LONDON_TEAM = ("ben.adeyemi", "chloe.fraser", "daniel.osei", "ella.marsh", "farid.rahman")
_DEMO_TEAM = ("ella.marsh", "farid.rahman", "hannah.okafor", "isaac.brennan", "jasmine.patel")

_ONE_OFFS = (
    # This week
    _b(0, 0, "10:00", 60, "London", "Thames", "Weekly planning", "anna.kowalski", *_LONDON_TEAM),
    _b(0, 0, "14:00", 30, "Manchester", "Deansgate", "1:1 Joanne / Kieran", "joanne.price", "kieran.walsh"),
    _b(0, 1, "11:00", 90, "Leeds", "Aire", "Quarterly numbers review", "tariq.mahmood",
       "ursula.finch", "victor.ambrose", "megan.rowntree", "wendy.carrick"),
    _b(0, 1, "13:00", 60, "London", "Fleet", "Design critique", "hannah.okafor",
       "isaac.brennan", "jasmine.patel", "grace.whitfield"),
    _b(0, 1, "15:00", 45, "Manchester", "Irwell", "Supplier call", "laura.nkemelu",
       "mohammed.siddiqui", "niamh.gallagher"),
    _b(0, 2, "10:00", 120, "London", "Thames", "Hiring panel", "grace.whitfield",
       "farid.rahman", "hannah.okafor", "joanne.price"),
    _b(0, 2, "12:00", 60, "Leeds", "Briggate", "Lunch and learn: accessibility", "yasmin.hollis",
       "zoe.pennington", "annabel.croft", "lewis.barnard", "xavier.lund"),
    _b(0, 2, "14:30", 30, "Manchester", "Ancoats", "Budget check-in", "priya.ramanathan", "joanne.price"),
    _b(0, 3, "09:00", 60, "Manchester", "Irwell", "Client workshop prep", "oliver.thorne",
       "quentin.hale", "rosie.dunmore", "sam.ellison"),
    _b(0, 3, "11:00", 30, "London", "Booth 1", "1:1 Anna / Ben", "anna.kowalski", "ben.adeyemi"),
    _b(0, 3, "14:00", 120, "London", "Thames", "North and South sync", "tariq.mahmood",
       "anna.kowalski", "joanne.price", "chloe.fraser"),
    _b(0, 3, "15:00", 30, "Leeds", "Kirkgate", "Interview: support engineer", "megan.rowntree", "lewis.barnard"),
    _b(0, 4, "10:30", 60, "Leeds", "Aire", "Retro", "ursula.finch",
       "victor.ambrose", "wendy.carrick", "xavier.lund", "yasmin.hollis"),
    _b(0, 4, "11:00", 45, "Manchester", "Deansgate", "Customer feedback review", "niamh.gallagher",
       "kieran.walsh", "laura.nkemelu"),
    _b(0, 4, "16:00", 60, "London", "Fleet", "Friday demo", "daniel.osei", *_DEMO_TEAM),
    # Next week
    _b(1, 0, "10:00", 60, "London", "Thames", "Weekly planning", "anna.kowalski", *_LONDON_TEAM),
    _b(1, 0, "13:30", 90, "Manchester", "Irwell", "Roadmap workshop", "joanne.price",
       "kieran.walsh", "laura.nkemelu", "mohammed.siddiqui", "oliver.thorne", "priya.ramanathan"),
    _b(1, 1, "10:00", 60, "Leeds", "Aire", "Office move planning", "tariq.mahmood",
       "megan.rowntree", "zoe.pennington"),
    _b(1, 1, "14:00", 30, "London", "Booth 1", "Contract review", "chloe.fraser", "grace.whitfield"),
    _b(1, 2, "11:00", 30, "Manchester", "Deansgate", "1:1 Joanne / Kieran", "joanne.price", "kieran.walsh"),
    _b(1, 2, "13:00", 120, "Leeds", "Briggate", "Training: new expenses tool", "annabel.croft",
       "ursula.finch", "victor.ambrose", "wendy.carrick", "xavier.lund", "yasmin.hollis", "lewis.barnard"),
    _b(1, 2, "15:00", 60, "London", "Fleet", "Design critique", "hannah.okafor",
       "isaac.brennan", "jasmine.patel", "grace.whitfield"),
    _b(1, 3, "09:45", 60, "London", "Thames", "All-hands rehearsal", "grace.whitfield",
       "anna.kowalski", "daniel.osei"),
    _b(1, 3, "12:00", 60, "Manchester", "Ancoats", "Lunch with new starters", "rosie.dunmore",
       "sam.ellison", "quentin.hale"),
    _b(1, 3, "14:00", 60, "Leeds", "Kirkgate", "Supplier call", "victor.ambrose", "wendy.carrick"),
    _b(1, 4, "10:00", 90, "Manchester", "Irwell", "Sprint review", "oliver.thorne",
       "quentin.hale", "rosie.dunmore", "sam.ellison", "priya.ramanathan", "hannah.okafor"),
    _b(1, 4, "15:30", 60, "Leeds", "Aire", "Friday wrap-up", "tariq.mahmood",
       "ursula.finch", "megan.rowntree", "annabel.croft"),
    _b(1, 4, "16:00", 60, "London", "Fleet", "Friday demo", "daniel.osei", *_DEMO_TEAM),
)

BOOKINGS: tuple[DemoBooking, ...] = _STANDUPS + _ONE_OFFS


class DemoError(Exception):
    """The demo data cannot be loaded into this database."""


@dataclass(frozen=True)
class DemoResult:
    rooms_added: int
    rooms_kept: int
    bookings_added: int
    bookings_skipped: int


def _email(local_part: str) -> str:
    return f"{local_part}@example.com"


def _people(session: Session) -> dict[str, Person]:
    """Every demo person by email local part, or DemoError naming the first one missing."""
    active = people_service.active_people_by_email(session)
    needed = {manager for manager, _ in OFFICES.values()}
    for booking in BOOKINGS:
        needed.update((booking.organiser, *booking.attendees))
    for local_part in sorted(needed):
        if _email(local_part) not in active:
            raise DemoError(
                f"demo bookings need the build seed: {_email(local_part)} is not an active person"
            )
    for office, (manager, _) in OFFICES.items():
        person = active[_email(manager)]
        if not (person.is_office_manager and person.home_office_name == office):
            raise DemoError(
                f"demo bookings need the build seed: {person.email} is not {office}'s office manager"
            )
    return {local_part: active[_email(local_part)] for local_part in needed}


def _rooms(session: Session, people: dict[str, Person]) -> tuple[dict[tuple[str, str], Room], int, int]:
    """Add the demo rooms each office lacks (name ignoring case); return them all by
    (office, name), and how many were added and kept."""
    rooms: dict[tuple[str, str], Room] = {}
    added = kept = 0
    for office, (manager, wanted) in OFFICES.items():
        actor = people[manager]
        existing = {r.name.casefold(): r for r in rooms_service.list_rooms(session, actor)}
        for name, capacity in wanted:
            room = existing.get(name.casefold())
            if room is None:
                room = rooms_service.add_room(session, actor, name, str(capacity))
                added += 1
            else:
                kept += 1
            rooms[(office, name)] = room
    return rooms, added, kept


def load_demo(session: Session) -> DemoResult:
    """Add the demo rooms and bookings, dated from today (UK). Checks every person first,
    so a database without the build seed gets nothing."""
    people = _people(session)
    rooms, rooms_added, rooms_kept = _rooms(session, people)
    monday = clock.week_start(clock.uk_now().date())
    added = skipped = 0
    for booking in BOOKINGS:
        room = rooms[(booking.office, booking.room)]
        organiser = people[booking.organiser]
        day = monday + timedelta(days=7 * booking.week + booking.weekday)
        start_at = clock.uk_to_utc(day, time.fromisoformat(booking.start))
        taken = any(
            other.room.id == room.id
            for other in bookings_service.bookings_in_slot(session, organiser, start_at, booking.minutes)
        )
        if taken or room.is_closed:
            skipped += 1
            continue
        try:
            bookings_service.book(
                session,
                organiser,
                room.id,
                start_at,
                booking.minutes,
                booking.title,
                [people[a].id for a in booking.attendees],
                allow_past=True,
            )
        except (bookings_service.BookingConflict, bookings_service.RoomClosed):
            skipped += 1  # someone booked it between the check and the insert
            continue
        added += 1
    return DemoResult(rooms_added, rooms_kept, added, skipped)
