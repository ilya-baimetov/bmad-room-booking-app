"""The one way to know who is using the app (AD-6), and which room a door tablet is for.

`current_person` is the only reader of the `person_id` cookie. When the cookie is
missing or names an unknown or inactive person it raises `NeedsPerson`, which the
handler registered in `app.py` turns into a trip to Pick your name and back.

`current_tablet` is the only reader of the `door_tablet` cookie (AD-8). It resolves the
cookie's token to the tablet's room, or to None, and never redirects.
"""

from typing import Annotated
from urllib.parse import quote, urlsplit

from fastapi import Depends, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from roombooker.core.db import get_session
from roombooker.core.settings import get_settings
from roombooker.people import service as people_service
from roombooker.people.service import Person
from roombooker.rooms import service as rooms_service
from roombooker.rooms.service import Room

COOKIE_NAME = "person_id"
COOKIE_MAX_AGE = 400 * 24 * 60 * 60  # 400 days
TABLET_COOKIE = "door_tablet"
PICK_PATH = "/pick-name"


class NeedsPerson(Exception):
    def __init__(self, next_url: str, clear_cookie: bool = False):
        super().__init__(next_url)
        self.next_url = next_url
        self.clear_cookie = clear_cookie


def path_with_query(request: Request) -> str:
    query = request.url.query
    return request.url.path + (f"?{query}" if query else "")


def pick_url(next_url: str) -> str:
    """URL of Pick your name that returns to `next_url` afterwards."""
    return f"{PICK_PATH}?next={quote(safe_next(next_url), safe='/')}"


def safe_next(next_url: str | None) -> str:
    """`next_url` when it is a local path, otherwise `/`."""
    if not next_url or not next_url.startswith("/") or next_url.startswith("//"):
        return "/"
    if "\\" in next_url or any(ord(ch) < 0x20 or ord(ch) == 0x7F for ch in next_url):
        return "/"
    parts = urlsplit(next_url)
    if parts.scheme or parts.netloc or parts.path.startswith(PICK_PATH):
        return "/"
    return next_url


def current_person(
    request: Request, session: Annotated[Session, Depends(get_session)]
) -> Person:
    """FastAPI dependency: the person using the app, or a redirect to Pick your name."""
    raw = request.cookies.get(COOKIE_NAME)
    person = None
    if raw is not None and raw.isascii() and raw.isdigit() and len(raw) <= 18:
        person = people_service.get_active_person(session, int(raw))
    if person is None:
        raise NeedsPerson(path_with_query(request), clear_cookie=raw is not None)
    return person


CurrentPerson = Annotated[Person, Depends(current_person)]


def remember_person(response: Response, person_id: int) -> None:
    """Set the `person_id` cookie (AD-6)."""
    response.set_cookie(
        COOKIE_NAME,
        str(person_id),
        max_age=COOKIE_MAX_AGE,
        path="/",
        httponly=True,
        samesite="lax",
        secure=get_settings().is_production,
    )


def forget_person(response: Response) -> None:
    """Clear the `person_id` cookie, e.g. when the browser becomes a door tablet."""
    response.delete_cookie(
        COOKIE_NAME,
        path="/",
        httponly=True,
        samesite="lax",
        secure=get_settings().is_production,
    )


def current_tablet(
    request: Request, session: Annotated[Session, Depends(get_session)]
) -> Room | None:
    """FastAPI dependency: the room this browser is the door tablet for, or None."""
    return rooms_service.tablet_room(session, request.cookies.get(TABLET_COOKIE))


CurrentTablet = Annotated[Room | None, Depends(current_tablet)]


def remember_tablet(response: Response, token: str) -> None:
    """Set the `door_tablet` cookie to a tablet's secret token (AD-8)."""
    response.set_cookie(
        TABLET_COOKIE,
        token,
        max_age=COOKIE_MAX_AGE,
        path="/",
        httponly=True,
        samesite="lax",
        secure=get_settings().is_production,
    )


async def needs_person_handler(request: Request, exc: NeedsPerson) -> Response:
    """htmx requests get `HX-Redirect`; full page loads get a 303."""
    target = pick_url(exc.next_url)
    if request.headers.get("HX-Request") == "true":
        response: Response = Response(status_code=200, headers={"HX-Redirect": target})
    else:
        response = RedirectResponse(target, status_code=303)
    if exc.clear_cookie:
        forget_person(response)
    return response
