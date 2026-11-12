---
title: "Office managers manage their office's rooms"
type: feature
ticket: '2'
created: '2026-11-12'
status: built
baseline_revision: '22bbc6afcf292099b9ee51e1e7190b9019a59f4b'
route: full
route_source: auto
risk: medium
review: quick
review_source: pinned
lenses_ran: [quick]
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/initiative-company-room-booking/ux-company-room-booking/DESIGN.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Office managers have nowhere to enter their office's rooms, so later epics have nothing to book and the rollout's "office managers check their rooms before go-live" cannot happen.

**Approach:** A `rooms` module (store, service, web) behind a Manage rooms tab: one office manager sees their home office's rooms table (name, capacity, Open/Closed) and adds, edits, closes (after one confirmation) and reopens rooms. Everyone else is refused by one RULE-4 predicate shared by the service and the templates. Refusals go through one core error handler.

## Boundaries & Constraints

**Always:**
- **AD-1 layering:** `rooms.web` calls `rooms.service` only. `rooms.service` calls `rooms.store` and `people.service`. `rooms.store` is imported only by `rooms.service`.
- **AD-3:** `rooms.service` is the only writer of `rooms`.
- **AD-7:** every write takes the acting `Person` and raises `NotAllowed` unless `can_manage_office(person, room_office_id)`, which means `is_office_manager` and `home_office_id == office_id`. Templates use the same predicate.
- **AD-10:** the table comes from Alembic revision `0002`.
- **AD-12:** `NotAllowed` → 403 with "Only office managers can manage rooms.", rendered by one handler in `core`.
- **Writes:** HTML form POSTs only, redirect-after-post on full page loads, fragments for htmx. Every route also works without JavaScript.
- **Logging:** every write logs the acting `person_id`, the action and the `room_id`.
- **Layout:** tap targets ≥ 44px. State is shown in words (Open/Closed). A closed row uses the `closed` grey, never red. On phone the table becomes a simple list.
- **Tabs (R9):** tabs show only for screens that exist, so the only tab is Manage rooms, shown only to office managers.
- **Landing:** after picking a name, an office manager lands on `/manage-rooms`; anyone else still sees "Booking opens soon.".

**Never:**
- Bookings of any kind, including the close confirmation's future-booking count and the `RoomClosed`, `BookingConflict` and `InvalidBooking` errors. Those are epic-find-and-book's.
- Deleting rooms.
- An office picker; an office manager manages only their home office.
- Editing status through Edit; status changes only through Close and Reopen.
- A JSON API, a JS framework, or browser `confirm()` dialogs.
- Editing people or offices.
- Deployment and CI.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| List | Office manager opens `/manage-rooms` | Their office's rooms sorted by name: name, capacity, Open/Closed; Add room form. Empty office: "No rooms in {office} yet." | No error |
| Add | Valid name + capacity | Room created Open in the actor's home office; appears in table | No error |
| Edit | Valid name + capacity for own-office room | Values updated; status unchanged | No error |
| Close | "Close" on an Open room | A confirmation naming the room; confirming makes it Closed, cancelling changes nothing | No error |
| Reopen | "Reopen" on a Closed room | Room shows Open | No error |
| Invalid | Empty/blank name; capacity blank, non-integer, < 1 or over the ceiling; name already used in the office (add or rename) | Nothing saved | 422; reason shown above the Save button; form keeps typed values |
| Not an office manager | Any person not managing that office: GET `/manage-rooms`, or POST add/edit/close/reopen (incl. office manager of another office on a room id) | No tab; page shows "Only office managers can manage rooms." | 403 via the AD-12 handler; nothing written |
| Unknown room id | POST or GET for a room id that does not exist | Nothing written | 404 |

**Decisions (user, 2026-11-12):**
- **Limits:** capacity is a whole number from 1 to 200; name is 1–50 characters after trimming.
- **Duplicates:** a name is a duplicate in its office when it matches another room's name ignoring case and surrounding spaces, on add and on rename.
- **Copy:**
  - Close confirmation: "Close {room}? No one can book it until you reopen it." with the buttons "Close room" and "Keep open".
  - Notices: "Added {room}.", "Saved {room}.", "Closed {room}.", "Reopened {room}.".
  - Reasons: "Give the room a name.", "Room names can be up to 50 characters.", "Capacity must be a whole number from 1 to 200." and "{office} already has a room called {name}.".

</frozen-after-approval>

## Code Map

Reuse from story 1. Don't change their behaviour except where noted.

- `roombooker/core/identity.py` -- `CurrentPerson`, `NeedsPerson` handler. Reuse it unchanged.
- `roombooker/people/service.py` -- `Person` (has `home_office_id`, `home_office_name`, `is_office_manager`). Add `can_manage_office(person, office_id) -> bool` here: the epic owns this check for later epics, and `bookings.service` will call it for RULE-3. It must not import `core.identity`.
- `roombooker/people/web.py` -- `landing` (`/`): redirect office managers to `/manage-rooms` (303). Other people still see `landing.html`. `_render` is the template helper pattern to copy.
- `roombooker/app.py` -- register the `rooms` router, the `DomainError` handler, and the `can_manage_office` Jinja global.
- `roombooker/templates/base.html` -- add a tab row in the top bar, `aria-current="page"` on the active tab, and an htmx config meta tag so 403 and 422 responses get swapped.
- `roombooker/static/app.css` -- tabs, rooms table/list, closed row, `.error-message`. Tokens already exist in `tokens.css` (`--color-closed`, `--color-error`, `--color-error-tint`, radii, `--touch-target`).
- `migrations/versions/0001_offices_people.py` -- the pattern for `0002_rooms.py`: hand-written, named constraints.
- `tests/conftest.py` -- `db_path`, `load_csv`, `client` (TestClient, `follow_redirects=False`). Set the `person_id` cookie on `client` to act as someone.
- `tests/e2e/conftest.py` -- `live_server` (build seed: London office managers Anna Kowalski and Grace Whitfield, Manchester Joanne Price, Leeds Tariq Mahmood and Megan Rowntree), `page` at both widths. `tests/e2e/test_pick_and_switch.py::pick` is the helper to reuse: move it into the conftest.
- New: `roombooker/core/errors.py`, `roombooker/rooms/{__init__,store,service,web}.py`, `roombooker/templates/rooms/`, `tests/test_rooms.py`, `tests/e2e/test_manage_rooms.py`.

## Tasks & Acceptance

**Execution:**
- [x] `migrations/versions/0002_rooms.py` -- create table `rooms(id, office_id FK offices NOT NULL, name NOT NULL, capacity INTEGER NOT NULL CHECK capacity >= 1, is_closed BOOLEAN NOT NULL DEFAULT false)` with `uq_rooms_office_id_name` -- AD-10, AD-4 needs `is_closed`.
- [x] `roombooker/core/errors.py` -- `DomainError(message)` with `status_code`, plus `NotAllowed(DomainError)` with status 403 and default message "Only office managers can manage rooms.". The handler renders `errors/refused.html` (full page, base layout, message in `#announce`). For htmx it returns the message fragment with `HX-Retarget: #announce` and `HX-Reswap: innerHTML` -- AD-12.
- [x] `roombooker/people/service.py` -- `can_manage_office` -- AD-7.
- [x] `roombooker/rooms/store.py` -- Table definition plus `list_for_office`, `get`, `insert`, `update_details`, `set_closed` -- AD-1, AD-3.
- [x] `roombooker/rooms/service.py` -- `Room` dataclass; `list_rooms(session, actor)`, `add_room`, `edit_room`, `close_room`, `reopen_room`, each taking `actor`. Each validates (trim; rules from the I/O matrix) and raises `InvalidRoom(errors, values)`. Not managing the office raises `NotAllowed`; an unknown id raises `RoomNotFound`. Each write commits and logs -- R3–R7.
- [x] `roombooker/rooms/web.py` + `templates/rooms/{manage,_table,_row,_edit_row,_confirm_close_row,_add_form}.html` -- `GET/HEAD /manage-rooms`, `POST /manage-rooms` (add), `GET /manage-rooms/{id}/edit`, `POST /manage-rooms/{id}`, `GET /manage-rooms/{id}/close` (confirmation), `POST /manage-rooms/{id}/close`, `POST /manage-rooms/{id}/reopen`. Full page loads get redirect-after-post to `/manage-rooms` with the result notice. htmx requests swap the row or form fragment. `InvalidRoom` re-renders the form at 422. `RoomNotFound` → 404 -- R3–R7, AD-2.
- [x] `base.html`, `people/web.py`, `app.py`, `app.css` -- tabs, landing redirect, wiring, styles -- R6, R9.
- [x] `tests/test_rooms.py` -- one test per I/O matrix row through `TestClient`, merging rows that need the same test. No test may repeat what another test already proves. Cover the log line once -- test policy.
- [x] `tests/e2e/test_manage_rooms.py` -- the ticket's verify at 1280×800 and 390×844. The rooms table persists across tests, so each test uses unique room names -- verify.
- [x] `README.md` -- one line: office managers land on Manage rooms.

**Acceptance Criteria:**
- Given the build seed, when Anna Kowalski picks her name, then she lands on Manage rooms for London with a Manage rooms tab, and Hannah Okafor (not an office manager) lands on "Booking opens soon." with no tabs.
- Given Anna on Manage rooms, when she adds a room, renames it and changes its capacity, closes it after confirming, then reopens it, then the table shows each result without a full page reload, at laptop and phone widths.
- Given JavaScript is off, when the same actions are submitted as plain forms, then each one works through redirect-after-post.
- Given Joanne Price (Manchester office manager), when she POSTs to close a London room, then she gets 403 and the room is unchanged.

## Implementation Notes

- **Story 1 test changed (forced by the landing redirect):** `test_pick_and_switch.py::test_switch_name_returns_to_same_page` switched between Anna and Tariq, who are both office managers, and expected `/?from=switch`. Now that `/` sends office managers to `/manage-rooms`, the test uses Chloe Fraser and Kieran Walsh, who are not office managers. Its assertions are unchanged. `pick` moved to `tests/e2e/conftest.py` as planned.
- **Notice after redirect:** the redirect goes to `/manage-rooms?notice=<added|saved|closed|reopened>&room=<id>`. The page builds the notice text from the room's name in the database, and only for a room in the actor's own office, so a crafted link cannot put text on the page.
- **Cancel / Keep open (htmx):** these use `hx-get="/manage-rooms"` with `hx-select="#room-<id>"` to put the row back, so no extra route is needed. Without JavaScript they are links to `/manage-rooms`.
- **No-JS edit and close pages:** these are `manage.html` with that one row shown as `_edit_row` or `_confirm_close_row` (the `editing_id` / `confirming_id` context).
- **Extra templates beyond the plan's list:** `rooms/_fragment.html` (an htmx fragment plus the out-of-band `#announce`, and the out-of-band table after an add), `rooms/_errors.html`, `errors/_message.html`.
- **`RoomNotFound` and `InvalidRoom`** subclass `DomainError` (404 and 422). `RoomNotFound` is rendered by the core handler. `InvalidRoom` is always caught in `rooms.web`.
- **Refused page top bar:** the AD-12 handler resolves the person through `core.identity.current_person` (lazy import) so the refused page still shows the name. It never redirects.
- **Capacity input** is `type="text" inputmode="numeric"` with no browser validation, so the server's reasons are the only ones a person sees. Room ids outside SQLite's INTEGER range return 404, not 500.
- **Refused attempts are also logged:** `rooms: person_id=… refused <action> for office_id=…`.
- **Verification:** `uv run pytest` gave 80 passed, e2e included, at both widths. `uv run alembic upgrade head` exited 0. The downgrade to 0001 and upgrade to head ran on a scratch DB through Alembic's Python API with `ROOMBOOKER_DB_PATH` set, not through the CLI.

## Plan Change Log

## Review Triage Log

**Pass 1 (2026-11-12, lens: quick).** Verdicts: high 0, medium 1, low 3, false 1, maybe-false 0. Routes: 3 patch, 0 defer, 0 loopback, 2 reject. After the patches: 80 tests pass (e2e at both widths), and the migration upgrade → downgrade 0001 → upgrade round trip works.

| # | Finding | Verdict | Route | Evidence / action |
|---|---------|---------|-------|-------------------|
| 1 | `base.html` switch link: switching from `/manage-rooms…` to a person who does not manage that office returns them to the 403 refusal page instead of "Booking opens soon." | medium | patch | Confirmed: `pick` redirects to `safe_next(next)` = `/manage-rooms`, and `list_rooms` raises `NotAllowed`. Fix: under `/manage-rooms` the link is `pick_url('/')`, and the landing redirect sends office managers back. Assertion added in `test_list_and_add`. |
| 2 | `rooms/web.py` `edit_room`: an htmx rename swaps only the row, so the table is no longer sorted by name until a reload | low | patch | Confirmed: the `hx-target="closest tr"` swap leaves the row in place. People rename rooms in everyday use, so this is not rejected. Fix: a successful htmx save returns `_table.html` with `HX-Retarget: #rooms-table` and the notice out of band. Edit test extended with a second room. |
| 3 | `rooms/web.py` `add_room`: an htmx add replaces `#rooms-table`, discarding a row that is open for edit or close confirmation, along with its typed values | low | reject | Real, but it needs a manager to leave Edit open and then use Add room. That is unlikely in everyday use, and the fix (keeping client state across the out-of-band swap) is more than a direct correction. |
| 4 | `core/errors.py`: a refusal or 404 after Cancel / Keep open (`hx-select="#room-<id>"`) empties `#announce` | low | patch | Confirmed in htmx 2.0.11: the element's `hx-select` applies unless `HX-Reselect` is set. It is rare (another tab or a reseed), but the fix is one header: `HX-Reselect: .error-message`. Asserted in `test_refusal_for_htmx_goes_to_announce`. |
| 5 | `tests/test_rooms.py` splits the Invalid and Not-an-office-manager rows over several tests, and the rename no-JS 422 repeats the add test | false | reject | Each split test proves a distinct behaviour: the backstop `IntegrityError` mapping, the htmx retarget headers, and the `edit_room` full-page `InvalidRoom` branch (a different route and code path from add). The test policy forbids repeated proofs, not more than one test per row. |

## Design Notes

The confirmation is server-rendered, not `confirm()`. "Close" fetches `_confirm_close_row` in place of the row, with the buttons "Close room" (secondary) and "Keep open". Without JavaScript it is its own page. This keeps it accessible and testable, and epic-find-and-book can add the future-booking count to that fragment.

A duplicate name is checked in the service with `casefold()` after trimming, because SQLite's `lower()` folds only ASCII. The exact-match unique constraint is a backstop: an `IntegrityError` is mapped to the same `InvalidRoom`.

htmx 2 does not swap 4xx responses by default, so `base.html` declares:
```html
<meta name="htmx-config" content='{"responseHandling":[{"code":"204","swap":false},{"code":"[23]..","swap":true},{"code":"40[34]|422","swap":true,"error":false},{"code":"...","swap":false,"error":true}]}'>
```

## Verification

**Commands:**
- `uv run alembic upgrade head` -- expected: exits 0, applies `0002`.
- `uv run pytest` -- expected: all pass, including the e2e tests at both widths and story 1's tests unchanged.
- `uv run alembic downgrade 0001 && uv run alembic upgrade head` (on a scratch `ROOMBOOKER_DB_PATH`) -- expected: both exit 0.
