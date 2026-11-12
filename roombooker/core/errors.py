"""Domain errors and the one handler that renders them (AD-12).

Services raise a `DomainError`; the handler registered in `app.py` turns it into a
response with the error's status code. Full page loads get `errors/refused.html`
(the base layout with the message in `#announce`). htmx requests get only the
message, retargeted into `#announce`.
"""

from fastapi import Request, Response


class DomainError(Exception):
    status_code = 400
    default_message = "That cannot be done."

    def __init__(self, message: str | None = None):
        self.message = message or self.default_message
        super().__init__(self.message)


class NotAllowed(DomainError):
    status_code = 403
    default_message = "Only office managers can manage rooms."


def _person_for_top_bar(request: Request):
    """The current person for the top bar, or None. Never redirects.

    Imported here so services can import this module without pulling in identity
    (which imports `people.service`).
    """
    from roombooker.core.db import get_session
    from roombooker.core.identity import NeedsPerson, current_person

    sessions = get_session()
    try:
        return current_person(request, next(sessions))
    except NeedsPerson:
        return None
    finally:
        sessions.close()


async def domain_error_handler(request: Request, exc: DomainError) -> Response:
    templates = request.app.state.templates
    if request.headers.get("HX-Request") == "true":
        response = templates.TemplateResponse(
            request,
            "errors/_message.html",
            {"message": exc.message},
            status_code=exc.status_code,
        )
        response.headers["HX-Retarget"] = "#announce"
        response.headers["HX-Reswap"] = "innerHTML"
        # Override any hx-select on the trigger (e.g. Cancel's `#room-<id>`).
        response.headers["HX-Reselect"] = ".error-message"
    else:
        response = templates.TemplateResponse(
            request,
            "errors/refused.html",
            {"message": exc.message, "person": _person_for_top_bar(request)},
            status_code=exc.status_code,
        )
    response.headers["Vary"] = "HX-Request"
    return response
