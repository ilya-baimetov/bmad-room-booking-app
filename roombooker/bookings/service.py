"""Bookings rules: free rooms, booking, seeing and cancelling bookings.

The only writer of `bookings` and `booking_attendees` (AD-3). Works in aware UTC
datetimes; the web layer converts UK time (AD-5). The database triggers refuse overlaps
and closed rooms (AD-4); this module turns their aborts into `BookingConflict` and
`RoomClosed`. Attendees are filled in only for the viewers AD-8 allows.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import Row
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from roombooker.bookings import store
from roombooker.core import time as clock
from roombooker.core.errors import DomainError, NotAllowed
from roombooker.people import service as people_service
from roombooker.people.service import Person, can_manage_office
from roombooker.rooms import service as rooms_service
from roombooker.rooms.service import Room

log = logging.getLogger("roombooker.bookings")

STEP_MINUTES = 15
LENGTH_MIN = 15
LENGTH_MAX = 4 * 60
DAYS_AHEAD = 90
TITLE_MAX_LENGTH = 100
UPCOMING_LIMIT = 20
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
    """A booking as one viewer may see it. `attendees` is empty unless AD-8 allows."""

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


def check_slot(start_at: datetime, length_minutes: int) -> datetime:
    """The slot's end, or InvalidBooking: on a quarter hour, 15 min to 4 h, from now to 90 days."""
    if start_at.second or start_at.microsecond or start_at.minute % STEP_MINUTES:
        raise InvalidBooking(NOT_ON_QUARTER)
    if not LENGTH_MIN <= length_minutes <= LENGTH_MAX or length_minutes % STEP_MINUTES:
        raise InvalidBooking(BAD_LENGTH)
    now = clock.utc_now()
    if start_at < now:
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


def _views(session: Session, viewer: Person, rows: list[Row]) -> list[BookingView]:
    if not rows:
        return []
    rooms = {room.id: room for room in rooms_service.all_rooms(session)}
    offices = people_service.office_names(session)
    attendees = {row.id: store.attendee_ids(session, row.id) for row in rows}
    names = people_service.names(
        session, {row.organiser_id for row in rows} | {i for ids in attendees.values() for i in ids}
    )
    views = []
    for row in rows:
        room = rooms[row.room_id]
        visible = can_see_attendees(viewer, row.organiser_id, room.office_id, attendees[row.id])
        views.append(
            BookingView(
                id=row.id,
                room=room,
                office_name=offices[room.office_id],
                start_at=clock.from_text(row.start_at),
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
                can_cancel=can_cancel_booking(viewer, row.organiser_id),
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


def room_to_book(session: Session, room_id: int) -> tuple[Room, str]:
    """The room and its office's name, for the booking form; RoomNotFound if none."""
    room = rooms_service.find_room(session, room_id)
    return room, people_service.office_names(session)[room.office_id]


def attendee_choices(
    session: Session, organiser: Person, chosen_ids: list[int], text: str
) -> tuple[list[tuple[int, str]], list[Person]]:
    """The chosen attendees as (id, name), dropping repeats, the organiser and unknown ids,
    and the active people matching `text` who could still be added."""
    chosen = [i for i in dict.fromkeys(chosen_ids) if i != organiser.id]
    names = people_service.names(session, chosen)
    chosen = [i for i in chosen if i in names]
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
) -> BookingView:
    """Book a room for the actor. The trigger is the guarantee against overlaps and
    closed rooms, even when two people book at once (AD-4)."""
    room = rooms_service.find_room(session, room_id)
    end_at = check_slot(start_at, length_minutes)
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
            raise RoomClosed(f"{room.name} is closed. Pick another room.") from None
        if "booking_conflict" in reason:
            raise BookingConflict(
                f"Someone has already booked {room.name} at that time. "
                "Pick another room or time."
            ) from None
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


def cancel(session: Session, actor: Person, booking_id: int) -> BookingView:
    """Cancel (delete, AD-13) the actor's own booking that has not ended yet."""
    view = booking_to_cancel(session, actor, booking_id)
    store.begin_immediate(session)
    store.delete_booking(session, booking_id)
    session.commit()
    log.info("bookings: person_id=%d cancel booking_id=%d", actor.id, booking_id)
    return view
