---
title: 'Pick and switch your name, end to end'
type: feature
ticket: '1'
created: '2026-11-12'
status: done
baseline_revision: '8a7db0e4b6c56313d521288e41b0d711f7bee930'
route: full
route_source: auto
risk: medium
review: quick
review_source: pinned
lenses_ran: [quick]
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/initiative-company-room-booking/architecture-company-room-booking/architecture-company-room-booking.md'
  - '{project-root}/_bmad-output/initiative-company-room-booking/ux-company-room-booking/DESIGN.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** There is no code yet. Every later story needs the app scaffold, the seeded people and offices, the page layout and one trusted way to know who is using the app.

**Approach:** A tracer bullet that runs locally. It scaffolds `roombooker` per the architecture Stack and Structural Seed, loads people from the R8 CSV, serves Pick your name with type-ahead inside the `base.html` layout, remembers the pick in the `person_id` cookie read only by `core.current_person`, and lets a person switch name from the top bar.

## Boundaries & Constraints

**Always:** AD-1 layering (seed CLI is the only other importer of `people.store`); AD-6 cookie `person_id` = `people.id`, 400 days, `HttpOnly`, `SameSite=Lax`, unsigned, `Secure` only when `ROOMBOOKER_ENV=production`; AD-10 schema only via Alembic; AD-11 pragmas `journal_mode=WAL`, `busy_timeout=5000`, `foreign_keys=ON` on every connection; settings only from `ROOMBOOKER_DB_PATH` (default `var/roombooker.db`) and `ROOMBOOKER_ENV` (default `local`); every route works on a full page load and enhances with htmx; DESIGN.md tokens as CSS custom properties; tap targets ≥ 44px, body text 16px; stdlib logging of each seed run and each pick, naming the `person_id`.

**Never:** rooms, bookings, tabs (R9: no screen exists yet), Docker/Caddy/Litestream, CI, a JSON API, a JS framework or bundler, a CSS framework, `create_all` outside tests, deleting people, editing people or offices in the app.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| First load | CSV `email,name,office,office_manager`; empty DB | Offices created by name; people inserted active; `office_manager` true for `true/yes/1` (any case), false for `false/no/0`/blank | No error |
| Reload | CSV drops person A, changes B's name, re-adds inactive C | A `active=false` with the same id; B updated in place (same id); C active again; offices never deleted | No error |
| Bad CSV | Missing column, duplicate email, unknown `office_manager` value, empty name or email | Nothing written | Non-zero exit, message names the row and problem |
| Search | `q="ann"` | Active people whose name contains it, case-insensitive, sorted by name, max 20, each with home office | Empty `q` shows "Start typing your name."; no match shows "No one called “{q}”." |
| Pick | POST person id + `next` | Cookie set; 303 to `next`, or `/` when absent | Inactive or unknown id → back to Pick your name; `next` that is not a local path (`//x`, `http://x`) → `/` |
| Guarded page | No cookie, junk cookie, unknown or inactive id | 303 to `/pick-name?next=<requested path+query>`; htmx request gets `HX-Redirect` instead | Bad cookie is cleared |

</frozen-after-approval>

## Code Map

The repo is empty apart from `README.md` and the BMad install (`_bmad/`, `.claude/`, `_bmad-output/`), so everything below is new. Follow the architecture Structural Seed tree and Consistency Conventions.

- `pyproject.toml`, `.python-version` (3.14), `uv.lock` -- the exact Stack pins (FastAPI 0.162.5, Uvicorn 0.54.0, Jinja2 3.1.6, python-multipart 0.0.33, SQLAlchemy 2.1.8, Alembic 1.20.1); dev group pytest 9.2.0, httpx 0.28.1, playwright 1.65.1, pytest-playwright 0.10.0 (all checked to resolve)
- `roombooker/core/` -- `settings.py`, `db.py` (engine + pragmas via a `connect` event, session dependency), `identity.py` (`current_person` dependency + the redirect exception and its handler). `identity.py` imports `people.service`; `people.service` must never import `core.identity`
- `roombooker/people/{store,service,web}.py` -- tables `offices(id, name unique)`, `people(id, email unique, name, home_office_id FK, is_office_manager, active)`; service exposes `search_active_people`, `get_active_person`; web serves `/pick-name` (GET page, GET fragment for htmx, POST pick) and `/` ("Booking opens soon.")
- `roombooker/seed.py` -- `python -m roombooker.seed <file.csv>`, one transaction
- `roombooker/app.py` -- app factory, static mount, Jinja env, exception handler
- `roombooker/templates/base.html`, `templates/people/` -- the layout: navy top bar with app name and current name linking to `/pick-name?next=<this page>`; `aria-live` region
- `roombooker/static/` -- `tokens.css` (every DESIGN.md token), `app.css`, `htmx.min.js` 2.0.11 (vendored)
- `migrations/`, `alembic.ini` -- `env.py` takes its URL from `core.settings`; first revision creates `offices` and `people`
- `seeds/build-people.csv` -- about 30 invented people (`@example.com`), roughly 10 per office, at least one office manager per office
- `tests/` -- `conftest.py` makes a temp DB migrated to head via Alembic; `e2e/` runs Uvicorn on a temp DB with Playwright
- `.gitignore` -- `var/`, `.venv/`, caches; `README.md` -- install, migrate, seed, run, test

## Tasks & Acceptance

**Execution:**
- [x] `pyproject.toml`, `.python-version`, `.gitignore`, `alembic.ini` -- uv project with the pins above, `uv lock` -- Stack is binding
- [x] `roombooker/core/settings.py`, `roombooker/core/db.py` -- settings and engine with AD-11 pragmas; create the parent folder of the DB path -- one way to configure and connect
- [x] `migrations/env.py`, `migrations/versions/0001_offices_people.py` -- the two tables, unique email and office name -- AD-10
- [x] `roombooker/people/store.py`, `roombooker/people/service.py` -- queries and the upsert used by seed; search and lookup for the web -- AD-1, AD-3
- [x] `roombooker/seed.py`, `seeds/build-people.csv` -- load/reload per the matrix -- R8, AD-9
- [x] `roombooker/core/identity.py` -- `current_person` and redirect handling per the matrix -- AD-6
- [x] `roombooker/app.py`, `roombooker/people/web.py`, templates, static -- picker with `hx-get` on input (`delay:200ms`) plus a plain GET form fallback; each result is a POST form button showing name and home office; `/` shows the name and "Booking opens soon." -- R1, R2
- [x] `tests/` -- one test per matrix row and per acceptance criterion through `TestClient`, plus Playwright e2e for the ticket's verify at 1280×800 and 390×844; no test may repeat what another test already proves -- test policy
- [x] `README.md` -- commands to install, migrate, seed, run and test -- the user's first local run

**Acceptance Criteria:**
- Given the build seed is loaded, when a person types part of a name on Pick your name and picks it, then the top bar shows that name, and still does after a browser reload.
- Given a person is on any page, when they choose their name in the top bar and pick another, then they return to the same page showing the new name.
- Given a person picked their name, when a reload of the seed drops them, then their next request goes to Pick your name, where they no longer appear, and everyone else's `people.id` is unchanged.
- Given a fresh checkout, when the README commands run in order, then the app serves Pick your name at `http://127.0.0.1:8000/`.

## Implementation Notes

- GET routes (`/`, `/pick-name`) also answer `HEAD`, so the Verification `curl -sI` gets the 303 rather than FastAPI's default 405.
- `/pick-name` is one URL for both the full page and the htmx fragment (fragment when `HX-Request: true`, `Vary: HX-Request`), so it works on a full page load.
- A refused pick (inactive, unknown or junk id) redirects to `/pick-name?next=...&gone=1`, which shows "That name is no longer in the list. Pick yours again." in the `aria-live` region; the notice uses navy tint, not error red (DESIGN.md keeps red for refused bookings and failed saves).
- `safe_next` also maps `next` values pointing back at `/pick-name`, containing backslashes or control characters, to `/`.
- The seed also refuses an empty office and a file with no people rows (so an empty file cannot mark everyone inactive). It reports every problem in the file, one per line, as `line N: problem`. Emails are lower-cased before matching.
- `migrations/env.py` does not import `people.store` (AD-1); migrations are hand-written, no autogenerate.
- The e2e harness starts the server with the README commands (alembic, seed, uvicorn) run with the venv's Python on a free port; the AC4 test checks `HEAD /` gives 303 to `/pick-name?next=/` and that it serves Pick your name.

## Plan Change Log

## Review Triage Log

**Pass 1 (2026-11-12, lens: quick).** Verdicts: high 0, medium 2, low 2, false 2, maybe-false 0. Routes: 4 patch, 0 defer, 0 loopback. After the patches: 34 tests pass, and `HEAD /` gives 303 to `/pick-name?next=/`.

| # | Finding | Verdict | Route | Evidence / action |
|---|---------|---------|-------|-------------------|
| 1 | `core/identity.py` `current_person`: an all-digit cookie too large for SQLite returns 500, not the redirect | medium | patch (with 2) | Reproduced: cookie `99999999999999999999` gave 500 and the cookie was never cleared. Fix: ids over 18 digits are junk; test case added. |
| 2 | `people/web.py` `pick`: the same overflow on the posted id | medium | patch (with 1) | Same root cause, an unbounded `int()` on the id. Reproduced: 25 digits gave 500. Same fix and a new test case. |
| 3 | `people/store.py` `search_active`: SQLite `lower()` folds only ASCII, so "Ó Briain" isn't found in another case | medium | patch | Reproduced: SQLite `lower('Ó Briain')` gives `'Ó briain'`. Fix: match and sort with Python `casefold()` over the active people; `test_search` extended. |
| 4 | `people/web.py` `pick_name`: `gone=x` returns a JSON 422 | low | patch | Reproduced the 422. Direct correction: `gone` is now a string compared with `"1"`. |
| 5 | `static/tokens.css`: component radius and min-height tokens are missing | low | patch | Real against the Code Map's "every DESIGN.md token". Aliases added, and `.button-*` now use them. Kept the single `--font-family`, since all four roles share one value. |
| 6 | The acceptance criteria have no TestClient tests, only e2e | false | reject | The acceptance criteria are the ticket's verify, which the plan assigns to Playwright e2e. Those tests ran and passed here (Chromium installed). Duplicating them in TestClient would break the test policy. |
| 7 | The e2e reload test repeats id assertions from `test_seed` | false | reject | The e2e test proves AC3 end to end with a real server and browser, which no other test does. The id check is part of AC3's own wording, not a repeated claim. |

## Design Notes

The landing page `/` belongs to `people.web` for now. Story 2 sends office managers to `/manage-rooms`, and epic-find-and-book replaces the landing with Rooms. Redirect through an exception raised by `current_person` and handled once in `app.py`, so no route checks identity itself:

```python
class NeedsPerson(Exception):
    def __init__(self, next_url: str): self.next_url = next_url
# handler: htmx -> 200 + HX-Redirect; else 303 Location=/pick-name?next=...; delete bad cookie
```

## Verification

**Commands:**
- `uv run alembic upgrade head && uv run python -m roombooker.seed seeds/build-people.csv` -- expected: exits 0, logs offices and people loaded
- `uv run pytest` -- expected: all pass, including e2e at both widths
- `uv run uvicorn roombooker.app:app` then `curl -sI http://127.0.0.1:8000/` -- expected: 303 to `/pick-name?next=/`

**Manual checks (if no CLI):**
- If Playwright's Chromium cannot be installed here, say so plainly; the e2e tests must still exist and run on the user's computer (`uv run playwright install chromium`).
