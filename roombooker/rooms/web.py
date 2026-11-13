"""Manage rooms: an office manager's rooms table, with add, edit, close and reopen (R3-R7),
and setting up and removing a room's door tablet.

Calls `rooms.service` only (AD-1). Every write is an HTML form POST: full page loads
get redirect-after-post to `/manage-rooms` with the result notice; htmx requests get
the row or form fragment, with the notice swapped into `#announce` out of band.
Setting up a door tablet is the exception: a plain form whose response turns this
browser into the tablet and sends it to `/door`.
`NotAllowed` and `RoomNotFound` go to the core handler (AD-12).
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse, Response
from sqlalchemy.orm import Session

from roombooker.core.db import get_session
from roombooker.core.identity import CurrentPerson, forget_person, remember_tablet
from roombooker.rooms import service
from roombooker.rooms.service import InvalidRoom, Room

router = APIRouter()

DbSession = Annotated[Session, Depends(get_session)]
FormText = Annotated[str, Form()]

PAGE = "/manage-rooms"
NOTICES = {
    "added": "Added {}.",
    "saved": "Saved {}.",
    "closed": "Closed {}.",
    "reopened": "Reopened {}.",
    "tablet_removed": "Removed the door tablet from {}.",
}
DOOR_PAGE = "/door"
CONFIRM_ROWS = {
    "close": "rooms/_confirm_close_row.html",
    "tablet": "rooms/_confirm_tablet_row.html",
    "remove_tablet": "rooms/_confirm_remove_tablet_row.html",
}


def _is_htmx(request: Request) -> bool:
    return request.headers.get("HX-Request") == "true"


def _render(request: Request, template: str, status_code: int = 200, **context) -> Response:
    response = request.app.state.templates.TemplateResponse(
        request, template, context, status_code=status_code
    )
    response.headers["Vary"] = "HX-Request"
    return response


def _page(
    request: Request,
    session: Session,
    person: service.Person,
    status_code: int = 200,
    **context,
) -> Response:
    """The full Manage rooms page. One row may be shown as its edit form or one of its
    confirmations (`confirming_kind`, a key of CONFIRM_ROWS)."""
    context.setdefault("notice", None)
    context.setdefault("editing_id", None)
    context.setdefault("confirming_id", None)
    context.setdefault("confirming_kind", "close")
    context.setdefault("edit_errors", [])
    context.setdefault("edit_values", None)
    context.setdefault("add_errors", [])
    context.setdefault("add_values", None)
    context["confirm_rows"] = CONFIRM_ROWS
    if "rooms" not in context:
        context["rooms"] = service.list_rooms(session, person)
    return _render(request, "rooms/manage.html", status_code, person=person, **context)


def _fragment(
    request: Request, template: str, notice: str | None = None, status_code: int = 200, **context
) -> Response:
    """An htmx fragment, plus `#announce` swapped out of band (the notice, or cleared)."""
    return _render(
        request, "rooms/_fragment.html", status_code, fragment=template, notice=notice, **context
    )


def _notice(action: str, room: Room) -> str:
    return NOTICES[action].format(room.name)


def _redirect(action: str, room: Room) -> Response:
    """Redirect-after-post; the page turns `notice` and `room` back into the notice."""
    return RedirectResponse(f"{PAGE}?notice={action}&room={room.id}", status_code=303)


def _row_done(request: Request, action: str, room: Room) -> Response:
    if _is_htmx(request):
        return _fragment(request, "rooms/_row.html", notice=_notice(action, room), room=room)
    return _redirect(action, room)


@router.api_route(PAGE, methods=["GET", "HEAD"])
def manage_rooms(
    request: Request,
    session: DbSession,
    person: CurrentPerson,
    notice: str = "",
    room: str = "",
) -> Response:
    rooms = service.list_rooms(session, person)
    # The notice names a room from the database, so a crafted link cannot put text on the page.
    named = next((r for r in rooms if str(r.id) == room), None)
    text = _notice(notice, named) if notice in NOTICES and named else None
    return _page(request, session, person, rooms=rooms, notice=text)


@router.post(PAGE)
def add_room(
    request: Request,
    session: DbSession,
    person: CurrentPerson,
    name: FormText = "",
    capacity: FormText = "",
) -> Response:
    try:
        room = service.add_room(session, person, name, capacity)
    except InvalidRoom as exc:
        if _is_htmx(request):
            return _fragment(
                request,
                "rooms/_add_form.html",
                status_code=422,
                errors=exc.errors,
                values=exc.values,
            )
        return _page(
            request,
            session,
            person,
            status_code=422,
            add_errors=exc.errors,
            add_values=exc.values,
        )
    if _is_htmx(request):
        # A fresh form, with the table (now holding the room, in name order) out of band.
        return _fragment(
            request,
            "rooms/_add_form.html",
            notice=_notice("added", room),
            errors=[],
            values=None,
            person=person,
            rooms=service.list_rooms(session, person),
            table_oob=True,
        )
    return _redirect("added", room)


@router.get(PAGE + "/{room_id:int}/edit")
def edit_form(
    request: Request, session: DbSession, person: CurrentPerson, room_id: int
) -> Response:
    room = service.get_room(session, person, room_id)
    if _is_htmx(request):
        return _render(request, "rooms/_edit_row.html", room=room, errors=[], values=None)
    return _page(request, session, person, editing_id=room.id)


@router.post(PAGE + "/{room_id:int}")
def edit_room(
    request: Request,
    session: DbSession,
    person: CurrentPerson,
    room_id: int,
    name: FormText = "",
    capacity: FormText = "",
) -> Response:
    try:
        room = service.edit_room(session, person, room_id, name, capacity)
    except InvalidRoom as exc:
        if _is_htmx(request):
            return _fragment(
                request,
                "rooms/_edit_row.html",
                status_code=422,
                room=service.get_room(session, person, room_id),
                errors=exc.errors,
                values=exc.values,
            )
        return _page(
            request,
            session,
            person,
            status_code=422,
            editing_id=room_id,
            edit_errors=exc.errors,
            edit_values=exc.values,
        )
    if _is_htmx(request):
        # A rename can move the row, so the whole table comes back in name order.
        response = _fragment(
            request,
            "rooms/_table.html",
            notice=_notice("saved", room),
            person=person,
            rooms=service.list_rooms(session, person),
        )
        response.headers["HX-Retarget"] = "#rooms-table"
        response.headers["HX-Reswap"] = "outerHTML"
        return response
    return _redirect("saved", room)


def _confirm(
    request: Request, session: Session, person: service.Person, room_id: int, kind: str
) -> Response:
    """Ask once: in place of the row for htmx, the page with the row asking otherwise."""
    room = service.get_room(session, person, room_id)
    if _is_htmx(request):
        return _render(request, CONFIRM_ROWS[kind], room=room)
    return _page(request, session, person, confirming_id=room.id, confirming_kind=kind)


@router.get(PAGE + "/{room_id:int}/close")
def confirm_close(
    request: Request, session: DbSession, person: CurrentPerson, room_id: int
) -> Response:
    return _confirm(request, session, person, room_id, "close")


@router.post(PAGE + "/{room_id:int}/close")
def close_room(
    request: Request, session: DbSession, person: CurrentPerson, room_id: int
) -> Response:
    return _row_done(request, "closed", service.close_room(session, person, room_id))


@router.post(PAGE + "/{room_id:int}/reopen")
def reopen_room(
    request: Request, session: DbSession, person: CurrentPerson, room_id: int
) -> Response:
    return _row_done(request, "reopened", service.reopen_room(session, person, room_id))


@router.get(PAGE + "/{room_id:int}/tablet")
def confirm_set_up_tablet(
    request: Request, session: DbSession, person: CurrentPerson, room_id: int
) -> Response:
    return _confirm(request, session, person, room_id, "tablet")


@router.post(PAGE + "/{room_id:int}/tablet")
def set_up_tablet(session: DbSession, person: CurrentPerson, room_id: int) -> Response:
    """This browser becomes the room's door tablet: it gets the tablet cookie, loses the
    person cookie, and goes to the door page (R9)."""
    _room, token = service.set_up_tablet(session, person, room_id)
    response = RedirectResponse(DOOR_PAGE, status_code=303)
    remember_tablet(response, token)
    forget_person(response)
    return response


@router.get(PAGE + "/{room_id:int}/tablet/remove")
def confirm_remove_tablet(
    request: Request, session: DbSession, person: CurrentPerson, room_id: int
) -> Response:
    return _confirm(request, session, person, room_id, "remove_tablet")


@router.post(PAGE + "/{room_id:int}/tablet/remove")
def remove_tablet(
    request: Request, session: DbSession, person: CurrentPerson, room_id: int
) -> Response:
    return _row_done(request, "tablet_removed", service.remove_tablet(session, person, room_id))
