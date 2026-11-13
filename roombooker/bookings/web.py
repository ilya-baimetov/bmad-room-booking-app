"""Rooms (find a free room), the booking form, booking details and cancelling, and a
room's door page with check-in.

Calls `bookings.service` only (AD-1), and `core.time` for UK time (AD-5). Every route
works on a full page load; htmx only narrows the swap with `hx-select` (AD-2).
Writes are form POSTs with redirect-after-post.

The door page knows the room only from the tablet cookie (`CurrentTablet`), never the
person, and links nowhere: its refusals are shown on the door page itself, not on the
app's refusal page with its top bar (AD-9).
"""

from datetime import datetime, timedelta
from typing import Annotated
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import RedirectResponse, Response
from sqlalchemy.orm import Session

from roombooker.bookings import service
from roombooker.bookings.service import (
    BookingConflict,
    InvalidBooking,
    RoomClosed,
)
from roombooker.core import time as uk
from roombooker.core.db import get_session
from roombooker.core.errors import DomainError
from roombooker.core.identity import CurrentPerson, CurrentTablet
from roombooker.people.service import Person

router = APIRouter()

DbSession = Annotated[Session, Depends(get_session)]
FormText = Annotated[str, Form()]

DEFAULT_LENGTH = 30
START_OPTIONS = [f"{h:02d}:{m:02d}" for h in range(24) for m in range(0, 60, 15)]
LENGTH_OPTIONS = [
    (str(minutes), uk.length_label(minutes))
    for minutes in range(service.LENGTH_MIN, service.LENGTH_MAX + 1, service.STEP_MINUTES)
]

NEEDS_DATE = "Pick a date."
NEEDS_START = "Pick a start time."
SKIPPED_TIME = "The clocks go forward then, so that time does not exist. Pick another."
BAD_CAPACITY = "People must be a whole number, or blank for any size."
NOTICES = {"cancelled": "Booking cancelled."}


def _render(request: Request, template: str, status_code: int = 200, **context) -> Response:
    response = request.app.state.templates.TemplateResponse(
        request, template, context, status_code=status_code
    )
    response.headers["Vary"] = "HX-Request"
    return response


def _whole(text: str, digits: int = 4) -> int | None:
    text = text.strip()
    return int(text) if text.isascii() and text.isdigit() and len(text) <= digits else None


def _slot(date_text: str, start_text: str, length_text: str) -> tuple[datetime, int]:
    """The UTC start and length in minutes of a UK date, clock time and length."""
    day = uk.parse_date(date_text)
    if day is None:
        raise InvalidBooking(NEEDS_DATE)
    start_clock = uk.parse_clock(start_text)
    if start_clock is None:
        raise InvalidBooking(NEEDS_START)
    length = _whole(length_text)
    if length is None:
        raise InvalidBooking(service.BAD_LENGTH)
    start_at = uk.uk_to_utc(day, start_clock)
    if start_at is None:
        raise InvalidBooking(SKIPPED_TIME)
    return start_at, length


def _slot_text(start_at: datetime, length: int) -> str:
    end_at = start_at + timedelta(minutes=length)
    return f"{uk.day(start_at)}, {uk.clock(start_at)}–{uk.clock(end_at)}"


def _attendee_ids(values: list[str]) -> list[int]:
    return [i for i in (_whole(v, 18) for v in values) if i is not None]


@router.api_route("/rooms", methods=["GET", "HEAD"])
def rooms(
    request: Request,
    session: DbSession,
    person: CurrentPerson,
    date: str = "",
    start: str = "",
    length: str = "",
    capacity: str = "",
    notice: str = "",
) -> Response:
    if not date and not start:
        first = uk.next_quarter_hour(uk.uk_now())
        date, start = first.date().isoformat(), first.strftime("%H:%M")
    length = length or str(DEFAULT_LENGTH)
    context = {
        "person": person,
        "values": {"date": date, "start": start, "length": length, "capacity": capacity},
        "start_options": START_OPTIONS,
        "length_options": LENGTH_OPTIONS,
        "notice": NOTICES.get(notice),
        "error": None,
        "groups": [],
        "in_slot": [],
        "slot_text": None,
        "book_query": None,
        "upcoming": service.upcoming_bookings(session, person),
    }
    status_code = 200
    try:
        start_at, minutes = _slot(date, start, length)
        min_capacity = _whole(capacity) if capacity.strip() else 1
        if min_capacity is None:
            raise InvalidBooking(BAD_CAPACITY)
        context["groups"] = service.free_rooms(session, person, start_at, minutes, min_capacity)
        context["in_slot"] = service.bookings_in_slot(session, person, start_at, minutes)
        context["slot_text"] = _slot_text(start_at, minutes)
        context["book_query"] = urlencode({"date": date, "start": start, "length": length})
    except InvalidBooking as exc:
        context["error"] = exc.message
        status_code = exc.status_code
    return _render(request, "bookings/rooms.html", status_code, **context)


def _form_page(
    request: Request,
    session: Session,
    person: Person,
    room_id: int,
    date: str,
    start: str,
    length: str,
    title: str | None,
    attendee_ids: list[int],
    q: str = "",
    error: str | None = None,
    status_code: int = 200,
    refused: str | None = None,
) -> Response:
    """`error` is announced alongside any slot problem the form finds; `refused` (a taken
    slot or closed room from POST) only when the form's own check no longer finds one."""
    room, office_name = service.room_to_book(session, room_id)
    attendees, found = service.attendee_choices(session, person, attendee_ids, q)
    slot_text = None
    problem = None
    try:
        start_at, minutes = _slot(date, start, length)
        slot_text = _slot_text(start_at, minutes)
        # A taken slot or closed room on GET stays 200: htmx swaps only 2xx (attendee search).
        problem = service.slot_problem(session, room.id, start_at, minutes)
    except InvalidBooking as exc:
        problem = exc.message
        status_code = status_code if status_code != 200 else exc.status_code
    if problem is not None:
        error = problem if not error or error == problem else f"{error} {problem}"
    error = error or refused
    return _render(
        request,
        "bookings/new.html",
        status_code,
        person=person,
        room=room,
        office_name=office_name,
        values={"date": date, "start": start, "length": length},
        slot_text=slot_text,
        title=f"{person.name}'s meeting" if title is None else title,
        attendees=attendees,
        q=q.strip(),
        found=found,
        error=error,
        pick_time=problem is not None,
        start_options=START_OPTIONS,
        length_options=LENGTH_OPTIONS,
    )


@router.api_route("/bookings/new", methods=["GET", "HEAD"])
def new_booking(
    request: Request,
    session: DbSession,
    person: CurrentPerson,
    room: str = "",
    date: str = "",
    start: str = "",
    length: str = "",
    title: str | None = None,
    attendee_id: Annotated[list[str], Query()] = [],  # noqa: B006 (FastAPI reads it)
    add: str = "",
    remove: str = "",
    q: str = "",
) -> Response:
    """The booking form. Adding, removing and searching attendees reload it (GET),
    keeping what was typed; htmx swaps in only the people results while typing."""
    ids = _attendee_ids(attendee_id)
    added = _whole(add, 18)
    if added is not None:
        ids.append(added)
        q = ""
    removed = _whole(remove, 18)
    ids = [i for i in ids if i != removed]
    return _form_page(
        request, session, person, _whole(room, 18) or 0, date, start, length, title, ids, q
    )


@router.post("/bookings")
def book(
    request: Request,
    session: DbSession,
    person: CurrentPerson,
    room: FormText = "",
    date: FormText = "",
    start: FormText = "",
    length: FormText = "",
    title: FormText = "",
    attendee_id: Annotated[list[str], Form()] = [],  # noqa: B006 (FastAPI reads it)
) -> Response:
    room_id = _whole(room, 18) or 0
    ids = _attendee_ids(attendee_id)
    try:
        start_at, minutes = _slot(date, start, length)
        booking = service.book(session, person, room_id, start_at, minutes, title, ids)
    except (InvalidBooking, BookingConflict, RoomClosed) as exc:
        slot_refusal = isinstance(exc, (BookingConflict, RoomClosed))
        return _form_page(
            request,
            session,
            person,
            room_id,
            date,
            start,
            length,
            title,
            ids,
            error=None if slot_refusal else exc.message,
            status_code=exc.status_code,
            refused=exc.message if slot_refusal else None,
        )
    return RedirectResponse(f"/bookings/{booking.id}?notice=booked", status_code=303)


@router.api_route("/bookings/{booking_id:int}", methods=["GET", "HEAD"])
def booking_details(
    request: Request, session: DbSession, person: CurrentPerson, booking_id: int, notice: str = ""
) -> Response:
    booking = service.get_booking(session, person, booking_id)
    text = None
    if notice == "booked" and booking.organiser_id == person.id:
        text = (
            f"Booked. {booking.room.name}, "
            f"{uk.clock(booking.start_at)}–{uk.clock(booking.end_at)}."
        )
    has_ended = booking.end_at <= uk.utc_now()
    return _render(
        request,
        "bookings/details.html",
        person=person,
        booking=booking,
        notice=text,
        has_ended=has_ended,
        confirming=False,
        book_again_query=_book_again_query(booking) if booking.organiser_id == person.id else None,
    )


@router.api_route("/bookings/{booking_id:int}/calendar.ics", methods=["GET", "HEAD"])
def booking_calendar(session: DbSession, person: CurrentPerson, booking_id: int) -> Response:
    """Add to calendar: the booking as a one-event .ics download, for anyone who can
    open its details page."""
    return Response(
        service.booking_calendar(session, person, booking_id),
        media_type="text/calendar; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="booking-{booking_id}.ics"'},
    )


def _book_again_query(booking: service.BookingView) -> str:
    """The booking form's query for the same room, UK clock time, length, title and
    attendees, on the UK date one week later."""
    day, start = uk.utc_to_uk(booking.start_at)
    minutes = int((booking.end_at - booking.start_at).total_seconds() // 60)
    return urlencode(
        {
            "room": booking.room.id,
            "date": (day + timedelta(days=7)).isoformat(),
            "start": start,
            "length": minutes,
            "title": booking.title,
            "attendee_id": list(booking.attendee_ids),
        },
        doseq=True,
    )


@router.get("/bookings/{booking_id:int}/cancel")
def confirm_cancel(
    request: Request, session: DbSession, person: CurrentPerson, booking_id: int
) -> Response:
    """Ask once before cancelling."""
    booking = service.booking_to_cancel(session, person, booking_id)
    return _render(
        request,
        "bookings/details.html",
        person=person,
        booking=booking,
        notice=None,
        has_ended=False,
        confirming=True,
        book_again_query=None,
    )


@router.post("/bookings/{booking_id:int}/cancel")
def cancel(
    request: Request, session: DbSession, person: CurrentPerson, booking_id: int
) -> Response:
    service.cancel(session, person, booking_id)
    return RedirectResponse("/rooms?notice=cancelled", status_code=303)


def _door(
    request: Request,
    session: Session,
    room: service.Room | None,
    message: str | None = None,
    status_code: int = 200,
) -> Response:
    """The door page for the tablet's room, or the not-set-up page when it has none."""
    return _render(
        request,
        "bookings/door.html",
        status_code,
        door=service.door_page(session, room) if room is not None else None,
        message=message,
    )


@router.api_route("/door", methods=["GET", "HEAD"])
def door(request: Request, session: DbSession, tablet: CurrentTablet) -> Response:
    return _door(request, session, tablet)


@router.post("/door/check-in/{booking_id:int}")
def door_check_in(
    request: Request, session: DbSession, tablet: CurrentTablet, booking_id: int
) -> Response:
    if tablet is None:
        return _door(request, session, None, status_code=403)
    try:
        service.check_in(session, tablet, booking_id)
    except DomainError as exc:
        return _door(request, session, tablet, exc.message, exc.status_code)
    return RedirectResponse("/door", status_code=303)
