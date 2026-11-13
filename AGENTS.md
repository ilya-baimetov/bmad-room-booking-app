<!-- bmad:context -->
<!-- Verified 2026-11-13 against 5f72d52. Managed by bmad-project-context; edits inside this block are replaced on refresh. Keep anything you want preserved outside the markers. -->

## room-booker

Internal room booking for the London, Manchester and Leeds offices: one FastAPI app, one SQLite file, server-rendered Jinja pages with htmx. `README.md` covers running, seeding, settings and tests; `docs/decisions/` holds the two surviving design records.

## Where things are

- Modules `people`, `rooms`, `bookings`, `calendar` under `roombooker/`, each split `web.py` → `service.py` → `store.py`; shared plumbing in `roombooker/core/`.
- Schema and DB triggers: `migrations/versions/`. Seed and demo data: `roombooker/seed.py`, `roombooker/demo.py`.

## Running and verifying

- Run Python only through `uv run`; the project pins Python 3.14 (`pyproject.toml`), which uv installs.
- Iterate with `uv run pytest --ignore=tests/e2e` (~7 s). `tests/e2e` takes ~1 min and needs `uv run playwright install chromium` once.

## Conventions that differ from defaults

- A `web.py` calls only its own module's service; never import another module's service or any `store.py` from a route.
- A `store.py` is imported only by its own service (`people.store` also by `seed.py`); go through the service.
- Service dependencies run one way: `bookings` → `rooms` → `people`, `calendar` → `bookings`. Never import the other way; put cross-module effects in the database (see the room-close trigger) or in the depending service.
- Write `rooms` only via `rooms.service` and `bookings`/`booking_attendees` only via `bookings.service`, including seed and demo code — its `begin_immediate` lock and the overlap triggers in `0003_bookings.py` are what stop double bookings.
- Closing a room deletes its future bookings in the trigger `rooms_close_cancels_future_bookings`; do not also delete them in Python (`docs/decisions/adr-closing-a-room-deletes-its-future-bookings.md`).
- A `Table` in a `store.py` only describes the schema; change tables with a new Alembic migration, never `metadata.create_all`.
- Get the time from `core.time.utc_now()`, never `datetime.now()`; store UTC text `YYYY-MM-DDTHH:MM:00Z`; convert UK↔UTC only in `core.time`.
- Compare names case-insensitively with `str.casefold()` in Python, never SQLite `lower()` or `COLLATE NOCASE` — SQLite folds only ASCII (`docs/decisions/adr-case-insensitive-matching-in-python-not-sqlite.md`).
- Read env vars only through `core.settings.get_settings()`; read the current person only through the `CurrentPerson` dependency.
- Every route must work as a full page load; htmx only narrows the swap with `hx-select`.
- Docstring citations `AD-n`, `RULE-n`, `Rn`, `OQ-n` point to a planning document that no longer exists. Do not search for it, and do not cite new ones; the docstrings and `docs/decisions/` are the record.

<!-- /bmad:context -->
