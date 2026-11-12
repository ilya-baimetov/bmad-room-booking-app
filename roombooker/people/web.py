"""Pick your name, and the landing page: office managers go on to Manage rooms, everyone
else to Rooms (R1, R2, R9)."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import RedirectResponse, Response
from sqlalchemy.orm import Session

from roombooker.core.db import get_session
from roombooker.core.identity import CurrentPerson, pick_url, remember_person, safe_next
from roombooker.people import service

log = logging.getLogger("roombooker.people")

router = APIRouter()

DbSession = Annotated[Session, Depends(get_session)]


def _render(request: Request, template: str, **context) -> Response:
    return request.app.state.templates.TemplateResponse(request, template, context)


@router.api_route("/", methods=["GET", "HEAD"])
def landing(person: CurrentPerson) -> Response:
    if service.can_manage_office(person, person.home_office_id):
        return RedirectResponse("/manage-rooms", status_code=303)
    return RedirectResponse("/rooms", status_code=303)


@router.api_route("/pick-name", methods=["GET", "HEAD"])
def pick_name(
    request: Request,
    session: DbSession,
    q: str = "",
    next_url: Annotated[str, Query(alias="next")] = "/",
    gone: str = "",
) -> Response:
    q = q.strip()
    context = {
        "q": q,
        "next": safe_next(next_url),
        "people": service.search_active_people(session, q),
        "gone": gone == "1",
    }
    is_htmx = request.headers.get("HX-Request") == "true"
    template = "people/_results.html" if is_htmx else "people/pick_name.html"
    response = _render(request, template, **context)
    response.headers["Vary"] = "HX-Request"
    return response


@router.post("/pick-name")
def pick(
    session: DbSession,
    person_id: Annotated[str, Form()] = "",
    next_url: Annotated[str, Form(alias="next")] = "/",
) -> Response:
    target = safe_next(next_url)
    person_id = person_id.strip()
    person = None
    if person_id.isascii() and person_id.isdigit() and len(person_id) <= 18:
        person = service.get_active_person(session, int(person_id))
    if person is None:
        log.info("pick refused: person_id=%r is unknown or inactive", person_id)
        return RedirectResponse(f"{pick_url(target)}&gone=1", status_code=303)

    response = RedirectResponse(target, status_code=303)
    remember_person(response, person.id)
    log.info("pick: person_id=%d picked their name, next=%s", person.id, target)
    return response
