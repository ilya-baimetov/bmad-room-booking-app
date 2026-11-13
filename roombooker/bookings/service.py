"""Bookings rules: free rooms, booking, seeing and cancelling bookings, the door page and
checking in.

The only writer of `bookings` and `booking_attendees` (AD-3). Works in aware UTC
datetimes; the web layer converts UK time (AD-5). The database triggers refuse overlaps
and closed rooms (AD-4); this module turns their aborts into `BookingConflict` and
`RoomClosed`. Attendees are filled in only for the viewers AD-8 allows.

A booking's check-in window is [start − CHECK_IN_OPENS, start + FREED_AFTER). Its
check-in state lives only here and is carried on `BookingView`: templates render it and
never recompute it. A booking is tracked only when its room's door tablet periods (from
`rooms.service`) cover its whole window.
"""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import Row
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from roombooker.bookings import ical, store
from roombooker.core import time as clock
from roombooker.core.errors import DomainError, NotAllowed
from roombooker.people import service as people_service
from roombooker.people.service import Person, can_manage_office
from roombooker.rooms import service as rooms_service
from roombooker.rooms.service import Room, TabletPeriod

log = logging.getLogger("roombooker.bookings")

CHECK_IN_OPENS = timedelta(minutes=5)  # before the start
FREED_AFTER = timedelta(minutes=15)  # after the start: the window closes then

UNTRACKED = "untracked"  # no tablet covered (or covers) the whole window
AWAITING = "awaiting"
CHECKED_IN = "checked_in"
FREED = "freed"

STEP_MINUTES = 15
LENGTH_MIN = 15
LENGTH_MAX = 4 * 60
DAYS_AHEAD = 90
TITLE_MAX_LENGTH = 100
UPCOMING_LIMIT = 20
FEED_DAYS_BACK = 30
FEED_NAME = "Room bookings"
FEED_END = datetime(9999, 12, 31, 23, 59, tzinfo=UTC)
SQLITE_MAX_INTEGER = 2**63 - 1

NOT_ON_QUARTER = "Bookings start on the hour or at 15, 30 or 45 minutes past."
BAD_LENGTH = "A booking lasts from 15 minutes to 4 hours, in 15-minute steps."
IN_THE_PAST = "That time has passed. Pick a later start."
TOO_FAR_AHEAD = f"You can book up to {DAYS_AHEAD} days ahead."
NEEDS_TITLE = "Give the booking a title."
TITLE_TOO_LONG = f"Titles can be up to {TITLE_MAX_LENGTH} characters."
ATTENDEE_GONE = "One of the attendees is no longer in the people list. Pick them again."
ONLY_ORGANISER = "Only the person who booked it can cancel it."
ALREADY_ENDED = "That booking has already ended."
CHECK_IN_NOT_OPEN = "Check-in opens at {}."
CHECK_IN_CLOSED = "Check-in closed at {}."
CHECK_IN_UNTRACKED = "This booking can't be checked in here."


class InvalidBooking(DomainError):
    status_code = 422


class BookingConflict(DomainError):
    status_code = 409


class RoomClosed(DomainError):
    status_code = 409


class BookingNotFound(DomainError):
    status_code = 404
    default_message = "That booking does not exist. It may have been cancelled."


@dataclass(frozen=True)
class BookingView:
    """A booking as one viewer may see it. `attendees` (names, sorted) and `attendee_ids`
    are empty unless AD-8 allows."""

    id: int
    room: Room
    office_name: str
    start_at: datetime
    end_at: datetime
    title: str
    organiser_id: int
    organiser_name: str
    attendees_visible: bool
    attendees: tuple[str, ...]
    can_cancel: bool
    attendee_ids: tuple[int, ...] = ()
    check_in: str = UNTRACKED  # UNTRACKED, AWAITING, CHECKED_IN or FREED (AD-7)
    check_in_opens_at: datetime | None = None
    freed_at: datetime | None = None
    can_check_in: bool = False  # tracked, not checked in or freed, and the window is open

    @property
    def check_in_closes_at(self) -> datetime:
        return self.start_at + FREED_AFTER


@dataclass(frozen=True)
class DoorPage:
    """What a room's door tablet shows: today's bookings (UK day), soonest first, with
    the current booking, or else the next one, marked."""

    room: Room
    bookings: tuple[BookingView, ...]
    marked_id: int | None
    marked_label: str | None  # "Now" or "Next"


@dataclass(frozen=True)
class OfficeRooms:
    office_id: int
    office_name: str
    is_own: bool
    rooms: tuple[Room, ...]


def can_cancel_booking(person: Person, organiser_id: int) -> bool:
    """Only the organiser cancels their booking."""
    return person.id == organiser_id


def can_see_attendees(person: Person, organiser_id: int, office_id: int, attendee_ids) -> bool:
    """AD-8: the organiser, the attendees and the room's office managers."""
    return (
        person.id == organiser_id
        or person.id in attendee_ids
        or can_manage_office(person, office_id)
    )


def check_slot(start_at: datetime, length_minutes: int, allow_past: bool = False) -> datetime:
    """The slot's end, or InvalidBooking: on a quarter hour, 15 min to 4 h, from now to 90 days.

    `allow_past` lifts only the "from now" rule, for the seed's demo bookings."""
    if start_at.second or start_at.microsecond or start_at.minute % STEP_MINUTES:
        raise InvalidBooking(NOT_ON_QUARTER)
    if not LENGTH_MIN <= length_minutes <= LENGTH_MAX or length_minutes % STEP_MINUTES:
        raise InvalidBooking(BAD_LENGTH)
    now = clock.utc_now()
    if start_at < now and not allow_past:
        raise InvalidBooking(IN_THE_PAST)
    if start_at > now + timedelta(days=DAYS_AHEAD):
        raise InvalidBooking(TOO_FAR_AHEAD)
    return start_at + timedelta(minutes=length_minutes)


def free_rooms(
    session: Session, viewer: Person, start_at: datetime, length_minutes: int, min_capacity: int
) -> list[OfficeRooms]:
    """Open rooms with at least `min_capacity` seats and no booking in the slot,
    by office (the viewer's own first, then by name), each sorted by name."""
    end_at = check_slot(start_at, length_minutes)
    taken = {
        row.room_id
        for row in store.overlapping(session, clock.to_text(start_at), clock.to_text(end_at))
    }
    offices = people_service.office_names(session)
    by_office: dict[int, list[Room]] = {}
    for room in rooms_service.all_rooms(session):
        if not room.is_closed and room.capacity >= min_capacity and room.id not in taken:
            by_office.setdefault(room.office_id, []).append(room)
    groups = [
        OfficeRooms(
            office_id,
            offices[office_id],
            office_id == viewer.home_office_id,
            tuple(sorted(rooms, key=lambda r: (r.name.casefold(), r.id))),
        )
        for office_id, rooms in by_office.items()
    ]
    groups.sort(key=lambda g: (not g.is_own, g.office_name.casefold()))
    return groups


def _covered(periods: list[TabletPeriod], start_at: datetime) -> bool:
    """Whether the tablet periods (in setup order; an active one has no end) cover the
    whole check-in window [start − 5 min, start + 15 min) without a gap (AD-6)."""
    cursor, closes = start_at - CHECK_IN_OPENS, start_at + FREED_AFTER
    for set_up_at, removed_at in sorted(periods, key=lambda period: period[0]):
        if set_up_at > cursor:
            break  # a gap before this period
        if removed_at is None or removed_at >= closes:
            return True
        cursor = max(cursor, removed_at)
    return False


def _check_in(row: Row, periods: list[TabletPeriod], now: datetime) -> tuple[str, bool]:
    """The booking's check-in state and whether it can be checked in now (AD-7)."""
    if row.freed_at is not None:
        return FREED, False
    if row.checked_in_at is not None:
        return CHECKED_IN, False
    start_at = clock.from_text(row.start_at)
    if not _covered(periods, start_at):
        return UNTRACKED, False
    return AWAITING, start_at - CHECK_IN_OPENS <= now < start_at + FREED_AFTER


def _views(session: Session, viewer: Person | None, rows: list[Row]) -> list[BookingView]:
    """Rows as `viewer` may see them. No viewer (the door tablet) sees no attendees and
    can cancel nothing."""
    if not rows:
        return []
    rooms = {room.id: room for room in rooms_service.all_rooms(session)}
    offices = people_service.office_names(session)
    periods = rooms_service.tablet_periods(session, {row.room_id for row in rows})
    now = clock.utc_now()
    attendees = {row.id: store.attendee_ids(session, row.id) for row in rows}
    names = people_service.names(
        session, {row.organiser_id for row in rows} | {i for ids in attendees.values() for i in ids}
    )
    views = []
    for row in rows:
        room = rooms[row.room_id]
        visible = viewer is not None and can_see_attendees(
            viewer, row.organiser_id, room.office_id, attendees[row.id]
        )
        start_at = clock.from_text(row.start_at)
        check_in, can_check_in = _check_in(row, periods.get(row.room_id, []), now)
        views.append(
            BookingView(
                id=row.id,
                room=room,
                office_name=offices[room.office_id],
                start_at=start_at,
                end_at=clock.from_text(row.end_at),
                title=row.title,
                organiser_id=row.organiser_id,
                organiser_name=names[row.organiser_id],
                attendees_visible=visible,
                attendees=(
                    tuple(sorted((names[i] for i in attendees[row.id]), key=str.casefold))
                    if visible
                    else ()
                ),
                can_cancel=viewer is not None and can_cancel_booking(viewer, row.organiser_id),
                attendee_ids=(
                    tuple(sorted(attendees[row.id], key=lambda i: (names[i].casefold(), i)))
                    if visible
                    else ()
                ),
                check_in=check_in,
                check_in_opens_at=start_at - CHECK_IN_OPENS,
                freed_at=clock.from_text(row.freed_at) if row.freed_at is not None else None,
                can_check_in=can_check_in,
            )
        )
    return views


def bookings_in_slot(
    session: Session, viewer: Person, start_at: datetime, length_minutes: int
) -> list[BookingView]:
    """Every booking that overlaps the slot, in any office, soonest first."""
    end_at = start_at + timedelta(minutes=length_minutes)
    rows = list(store.overlapping(session, clock.to_text(start_at), clock.to_text(end_at)))
    return _views(session, viewer, rows)


def upcoming_bookings(session: Session, viewer: Person) -> list[BookingView]:
    """The viewer's own bookings that have not ended, soonest first (at most 20)."""
    rows = store.upcoming_for_organiser(
        session, viewer.id, clock.to_text(clock.utc_now()), UPCOMING_LIMIT
    )
    return _views(session, viewer, list(rows))


def bookings_for_person(
    session: Session, viewer: Person, start_at: datetime, end_at: datetime
) -> list[BookingView]:
    """The viewer's bookings, organised or attended, overlapping [start_at, end_at),
    soonest first."""
    rows = store.for_person(session, viewer.id, clock.to_text(start_at), clock.to_text(end_at))
    return _views(session, viewer, list(rows))


def _closed_message(room: Room) -> str:
    return f"{room.name} is closed. Pick another room."


def _taken_message(room: Room, choice: str = "another room or time") -> str:
    return f"Someone has already booked {room.name} at that time. Pick {choice}."


def slot_problem(
    session: Session, room_id: int, start_at: datetime, length_minutes: int
) -> str | None:
    """Why the room can't be booked for the slot right now, or None if it can.

    Raises InvalidBooking when the slot itself breaks a rule (`check_slot`); returns the
    closed-room or taken-slot message otherwise. Advisory only, for the booking form:
    `book` and the triggers stay the guarantee. Writes nothing."""
    room = rooms_service.find_room(session, room_id)
    if room.is_closed:
        return _closed_message(room)
    end_at = check_slot(start_at, length_minutes)
    rows = store.overlapping(session, clock.to_text(start_at), clock.to_text(end_at))
    if any(row.room_id == room.id for row in rows):
        return _taken_message(room, "another time")  # the form shows the time pickers
    return None


def room_to_book(session: Session, room_id: int) -> tuple[Room, str]:
    """The room and its office's name, for the booking form; RoomNotFound if none."""
    room = rooms_service.find_room(session, room_id)
    return room, people_service.office_names(session)[room.office_id]


def attendee_choices(
    session: Session, organiser: Person, chosen_ids: list[int], text: str
) -> tuple[list[tuple[int, str]], list[Person]]:
    """The chosen attendees as (id, name), dropping repeats, the organiser and unknown or
    inactive ids, and the active people matching `text` who could still be added."""
    chosen = [i for i in dict.fromkeys(chosen_ids) if i != organiser.id]
    names = people_service.names(session, chosen)
    chosen = [
        i for i in chosen if i in names and people_service.get_active_person(session, i)
    ]
    found = [
        p
        for p in people_service.search_active_people(session, text)
        if p.id != organiser.id and p.id not in chosen
    ]
    return [(i, names[i]) for i in chosen], found


def _get_row(session: Session, booking_id: int) -> Row:
    row = store.get(session, booking_id) if 0 < booking_id <= SQLITE_MAX_INTEGER else None
    if row is None:
        raise BookingNotFound()
    return row


def get_booking(session: Session, viewer: Person, booking_id: int) -> BookingView:
    """One booking, as the viewer may see it. Anyone may look."""
    return _views(session, viewer, [_get_row(session, booking_id)])[0]


def booking_calendar(session: Session, viewer: Person, booking_id: int) -> str:
    """One booking as an iCalendar file's text, for anyone who may look at it.
    No attendees are written, whoever the viewer is."""
    return ical.calendar([get_booking(session, viewer, booking_id)], clock.utc_now())


def feed_calendar(session: Session, person: Person) -> str:
    """The person's subscribed feed: the bookings they organise or attend that end after
    30 days ago, as a named iCalendar text. No attendees are written."""
    now = clock.utc_now()
    events = bookings_for_person(session, person, now - timedelta(days=FEED_DAYS_BACK), FEED_END)
    return ical.calendar(events, now, name=FEED_NAME)


def _clean_title(title: str) -> str:
    clean = " ".join(title.split())
    if not clean:
        raise InvalidBooking(NEEDS_TITLE)
    if len(clean) > TITLE_MAX_LENGTH:
        raise InvalidBooking(TITLE_TOO_LONG)
    return clean


def book(
    session: Session,
    actor: Person,
    room_id: int,
    start_at: datetime,
    length_minutes: int,
    title: str,
    attendee_ids: list[int],
    allow_past: bool = False,
) -> BookingView:
    """Book a room for the actor. The trigger is the guarantee against overlaps and
    closed rooms, even when two people book at once (AD-4). Only the seed's demo
    bookings pass `allow_past`; the web never does."""
    room = rooms_service.find_room(session, room_id)
    end_at = check_slot(start_at, length_minutes, allow_past)
    clean_title = _clean_title(title)
    attendees = []
    for person_id in dict.fromkeys(attendee_ids):  # keep order, drop repeats
        if person_id == actor.id:
            continue  # the organiser is there anyway
        if people_service.get_active_person(session, person_id) is None:
            raise InvalidBooking(ATTENDEE_GONE)
        attendees.append(person_id)

    store.begin_immediate(session)
    try:
        booking_id = store.insert(
            session,
            room.id,
            actor.id,
            clean_title,
            clock.to_text(start_at),
            clock.to_text(end_at),
            attendees,
        )
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        reason = str(exc.orig)
        log.info(
            "bookings: person_id=%d refused book room_id=%d (%s)", actor.id, room.id, reason
        )
        if "room_closed" in reason:
            raise RoomClosed(_closed_message(room)) from None
        if "booking_conflict" in reason:
            raise BookingConflict(_taken_message(room)) from None
        raise
    log.info("bookings: person_id=%d book booking_id=%d room_id=%d", actor.id, booking_id, room.id)
    return get_booking(session, actor, booking_id)


def booking_to_cancel(session: Session, actor: Person, booking_id: int) -> BookingView:
    """The actor's own booking that has not ended, for the cancel confirmation."""
    view = get_booking(session, actor, booking_id)
    if not view.can_cancel:
        log.info("bookings: person_id=%d refused cancel booking_id=%d", actor.id, booking_id)
        raise NotAllowed(ONLY_ORGANISER)
    if view.end_at <= clock.utc_now():
        raise InvalidBooking(ALREADY_ENDED)
    return view


def door_page(session: Session, room: Room) -> DoorPage:
    """The room's bookings for today (UK day), for its door tablet."""
    today = clock.uk_now().date()
    rows = store.in_room(
        session,
        room.id,
        clock.to_text(clock.uk_midnight(today)),
        clock.to_text(clock.uk_midnight(today + timedelta(days=1))),
    )
    views = _views(session, None, list(rows))
    now = clock.utc_now()
    current = next((v for v in views if v.start_at <= now < v.end_at), None)
    upcoming = next((v for v in views if v.start_at > now), None)
    marked, label = (current, "Now") if current else (upcoming, "Next")
    return DoorPage(
        room=room,
        bookings=tuple(views),
        marked_id=marked.id if marked else None,
        marked_label=label if marked else None,
    )


def check_in(session: Session, room: Room, booking_id: int) -> BookingView:
    """Check in one of the room's bookings from its door tablet, anonymously (AD-7).

    Accepted from start − 5 min until start + 15 min, for a booking the room's tablets
    cover; checking in again is a success that keeps the first time. Runs under the
    write lock and decides on the row as re-read inside it (AD-2)."""
    if _get_row(session, booking_id).room_id != room.id:
        raise BookingNotFound()
    store.begin_immediate(session)
    try:
        row = _get_row(session, booking_id)
        now = clock.utc_now()
        start_at = clock.from_text(row.start_at)
        periods = rooms_service.tablet_periods(session, [room.id]).get(room.id, [])
        state, can_check_in = _check_in(row, periods, now)
        checked_in_now = state == AWAITING and can_check_in
        if checked_in_now:
            store.set_checked_in(session, booking_id, clock.to_text(now))
        elif state == FREED:
            raise InvalidBooking(CHECK_IN_CLOSED.format(clock.clock(start_at + FREED_AFTER)))
        elif state == UNTRACKED:
            raise InvalidBooking(CHECK_IN_UNTRACKED)
        elif state == AWAITING and now < start_at - CHECK_IN_OPENS:
            raise InvalidBooking(CHECK_IN_NOT_OPEN.format(clock.clock(start_at - CHECK_IN_OPENS)))
        elif state == AWAITING:
            raise InvalidBooking(CHECK_IN_CLOSED.format(clock.clock(start_at + FREED_AFTER)))
        session.commit()  # also ends the lock when it was already checked in
    except BaseException:
        session.rollback()
        raise
    if checked_in_now:
        log.info("bookings: check in booking_id=%d room_id=%d", booking_id, room.id)
    return _views(session, None, [_get_row(session, booking_id)])[0]


def cancel(session: Session, actor: Person, booking_id: int) -> BookingView:
    """Cancel (delete, AD-13) the actor's own booking that has not ended yet."""
    view = booking_to_cancel(session, actor, booking_id)
    store.begin_immediate(session)
    store.delete_booking(session, booking_id)
    session.commit()
    log.info("bookings: person_id=%d cancel booking_id=%d", actor.id, booking_id)
    return view
