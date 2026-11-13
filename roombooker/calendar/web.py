"""My bookings: the current person's bookings by day and by week, today highlighted, and
their private calendar feed.

Calls `calendar.service` only (AD-1), and `core.time` for UK days (AD-5). Navigation is
plain links, so every view is a full page load (AD-2). Creating or resetting the feed
address is a form POST with redirect-after-post.

The feed itself (`/feeds/<token>.ics`) is fetched by calendar apps with no cookie, so it
finds its person from the token alone, never from `CurrentPerson`.
"""

import re
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Annotated
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import PlainTextResponse, RedirectResponse, Response
from sqlalchemy.orm import Session

from roombooker.bookings.service import BookingView
from roombooker.calendar import service
from roombooker.core import time as uk
from roombooker.core.db import get_session
from roombooker.core.identity import CurrentPerson

router = APIRouter()

DbSession = Annotated[Session, Depends(get_session)]

VIEWS = ("day", "week")
EARLIEST = date(1900, 1, 1)
LATEST = date(9000, 12, 31)
TOKEN = re.compile(r"[A-Za-z0-9_-]{43}")  # secrets.token_urlsafe(32)
NOTICES = {
    "feed-created": "Your calendar feed address is ready.",
    "feed-reset": "Your feed address has been reset. The old address has stopped working.",
}


@dataclass(frozen=True)
class Day:
    date: date
    label: str
    is_today: bool
    bookings: tuple[BookingView, ...]


def _url(view: str, day: date) -> str:
    return "/my-bookings?" + urlencode({"view": view, "date": day.isoformat()})


def _label(day: date) -> str:
    """`Tue 17 Nov`, from a UK date."""
    return f"{day:%a} {day.day} {day:%b}"


def _empty_text(view: str, first: date, today: date) -> str:
    if view == "day":
        return "No bookings today." if first == today else f"No bookings on {_label(first)}."
    if first <= today < first + timedelta(days=7):
        return "No bookings this week."
    return f"No bookings in the week of {_label(first)}."


@router.api_route("/my-bookings", methods=["GET", "HEAD"])
def my_bookings(
    request: Request,
    session: DbSession,
    person: CurrentPerson,
    view: str = "day",
    date: str = "",
    notice: str = "",
) -> Response:
    today = uk.uk_now().date()
    view = view if view in VIEWS else "day"
    chosen = uk.parse_date(date) or today
    if not EARLIEST <= chosen <= LATEST:  # keep date arithmetic in range
        chosen = today
    first = uk.week_start(chosen) if view == "week" else chosen
    count = 7 if view == "week" else 1
    dates = [first + timedelta(days=i) for i in range(count)]
    bounds = [uk.uk_midnight(d) for d in [*dates, dates[-1] + timedelta(days=1)]]
    bookings = service.my_bookings(session, person, bounds[0], bounds[-1])
    days = [
        Day(
            date=d,
            label=_label(d),
            is_today=d == today,
            bookings=tuple(b for b in bookings if b.start_at < bounds[i + 1] and b.end_at > bounds[i]),
        )
        for i, d in enumerate(dates)
    ]
    step = timedelta(days=count)
    token = service.feed_address_token(session, person)
    if view == "week":
        heading = f"Week of {_label(first)}"
    else:
        heading = f"Today, {_label(first)}" if first == today else _label(first)
    return request.app.state.templates.TemplateResponse(
        request,
        "calendar/my_bookings.html",
        {
            "person": person,
            "view": view,
            "heading": heading,
            "days": days,
            "is_empty": not bookings,
            "empty_text": _empty_text(view, first, today),
            "day_url": _url("day", chosen),
            "week_url": _url("week", chosen),
            "previous_url": _url(view, chosen - step),
            "next_url": _url(view, chosen + step),
            "today_url": _url(view, today),
            "previous_label": "Previous week" if view == "week" else "Previous day",
            "next_label": "Next week" if view == "week" else "Next day",
            "feed_url": _feed_url(request, token) if token else None,
            "notice": NOTICES.get(notice),
        },
    )


def _feed_url(request: Request, token: str) -> str:
    """The absolute feed address, from the host the request came to (behind a TLS proxy,
    run uvicorn with `--proxy-headers` so this is `https://`)."""
    return str(request.base_url).rstrip("/") + f"/feeds/{token}.ics"


@router.get("/my-bookings/feed/reset")
def confirm_reset_feed(request: Request, session: DbSession, person: CurrentPerson) -> Response:
    """Ask once before replacing the feed address. With no address yet there is nothing
    to reset, so back to My bookings."""
    if service.feed_address_token(session, person) is None:
        return RedirectResponse("/my-bookings", status_code=303)
    return request.app.state.templates.TemplateResponse(
        request, "calendar/confirm_reset.html", {"person": person}
    )


@router.post("/my-bookings/feed")
def reset_feed(
    session: DbSession, person: CurrentPerson, replace: Annotated[str, Form()] = ""
) -> Response:
    """Create the viewer's feed address, or replace it (the old one stops working) when
    the reset confirmation sent `replace=1`. A Create from a stale page while an address
    exists goes to the confirmation instead of replacing it silently."""
    had_token = service.feed_address_token(session, person) is not None
    if had_token and replace != "1":
        return RedirectResponse("/my-bookings/feed/reset", status_code=303)
    service.reset_feed(session, person)
    notice = "feed-reset" if had_token else "feed-created"
    return RedirectResponse(f"/my-bookings?notice={notice}", status_code=303)


@router.api_route("/feeds/{name:path}", methods=["GET", "HEAD"])
def feed(session: DbSession, name: str) -> Response:
    """A person's bookings as a subscribed calendar. An unknown, malformed, replaced or
    inactive person's token is a plain 404: the app reports an error, and nothing says
    whether the token ever existed."""
    token = name.removesuffix(".ics") if name.endswith(".ics") else ""
    text = service.feed(session, token) if TOKEN.fullmatch(token) else None
    if text is None:
        return PlainTextResponse("Not found", status_code=404)
    return Response(
        text,
        media_type="text/calendar; charset=utf-8",
        headers={"Cache-Control": "private, no-cache"},
    )
