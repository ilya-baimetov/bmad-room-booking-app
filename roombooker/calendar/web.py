"""My bookings: the current person's bookings by day and by week, today highlighted.

Calls `calendar.service` only (AD-1), and `core.time` for UK days (AD-5). Navigation is
plain links, so every view is a full page load (AD-2).
"""

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Annotated
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response
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
        },
    )
