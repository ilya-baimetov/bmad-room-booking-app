"""Application factory: routes, static files, templates and the identity redirect."""

import logging
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from roombooker.core.identity import NeedsPerson, needs_person_handler, path_with_query, pick_url
from roombooker.people import web as people_web

PACKAGE_DIR = Path(__file__).parent


def _configure_logging() -> None:
    logger = logging.getLogger("roombooker")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
        logger.addHandler(handler)


def create_app() -> FastAPI:
    _configure_logging()
    app = FastAPI(title="Room Booking", docs_url=None, redoc_url=None, openapi_url=None)

    templates = Jinja2Templates(directory=PACKAGE_DIR / "templates")
    templates.env.globals["pick_url"] = pick_url
    templates.env.globals["path_with_query"] = path_with_query
    app.state.templates = templates

    app.mount("/static", StaticFiles(directory=PACKAGE_DIR / "static"), name="static")
    app.add_exception_handler(NeedsPerson, needs_person_handler)
    app.include_router(people_web.router)
    return app


app = create_app()
