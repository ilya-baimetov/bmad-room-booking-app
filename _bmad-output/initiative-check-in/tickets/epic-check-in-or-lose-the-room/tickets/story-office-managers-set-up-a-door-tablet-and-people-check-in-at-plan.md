---
title: 'Office managers set up a door tablet and people check in at it'
type: feature
ticket: '1'
created: '2026-11-13'
status: ready-for-dev
baseline_revision: ''
route: full
route_source: auto
risk: medium
review: ''
review_source: ''
lenses_ran: []
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/initiative-check-in/tickets/epic-check-in-or-lose-the-room/epic-check-in-or-lose-the-room.md'
  - '{project-root}/_bmad-output/initiative-check-in/architecture-check-in/architecture-check-in.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Rooms have no door tablet and bookings have no check-in, so nothing can later tell a claimed booking from an abandoned one (epic R1–R3, R9, R10).

**Approach:** Tracer bullet through every layer: migration 0005, tablet setup, replacement and removal on Manage rooms, a `door_tablet` credential, a plain `/door` page listing the room's bookings for today, and one-tap anonymous check-in inside start − 5 to start + 15, with the check-in state on `BookingView` for later stories.

## Boundaries & Constraints

**Always:** AD-1 module rules (`rooms` owns `room_tablets`; `bookings` gets tablet periods only from `rooms.service`; door routes in `bookings.web`; tablet setup in `rooms.web`). Check-in is a `bookings.service` write inside `store.begin_immediate`, re-reading the row after the lock (AD-2). Time from `clock.utc_now()` only, stored as `YYYY-MM-DDTHH:MM:00Z`; UK day via `core.time`. The door page never uses `CurrentPerson` and links nowhere (no top bar, no app name link). Every route works as a full page load; POSTs redirect 303. One log line per setup, removal and check-in, ids only, never the token. Window constants `CHECK_IN_OPENS = 5 min`, `FREED_AFTER = 15 min` live in `bookings.service` (AD-7).

**Never:** freeing, writing `freed_at`, or any "freed"/countdown wording (story 2/3); the styled door screen, polling or back-to-back button (story 3); check-in tags on My bookings or details (story 4); booking from the door; a batch/rebuild migration of `bookings` (it would drop the overlap triggers and cascade-delete attendees); `metadata.create_all`; `datetime.now()`.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Setup | Manager of the room's office confirms "Set up door tablet" | `door_tablet` cookie set, `person_id` cookie cleared, previous active tablet of that room gets `removed_at` = now, 303 to `/door` | Non-manager: existing `NotAllowed` |
| Replace | Room already has an active tablet; setup in another browser | Old tablet's next `/door` shows not-set-up page; new one shows the room | — |
| Remove | Manager confirms Remove on the row | `removed_at` = now; that browser's `/door` shows not-set-up page; row says "No door tablet" | Non-manager: `NotAllowed` |
| No credential | `/door` with no, unknown or removed token | Plain page: "This tablet isn't set up for a room. Ask your office manager to set it up." | — |
| Check in, window open | now in [start − 5, start + 15), not checked in | `checked_in_at` = now, 303 to `/door`, row shows "✓ Checked in" | — |
| Repeat tap | already checked in | Treated as success, unchanged `checked_in_at` | — |
| Outside window | now < start − 5 or ≥ start + 15 | No Check in button; forced POST refused, door page re-rendered with the refusal, no link out | `InvalidBooking` |
| Wrong room / no booking | booking not in the tablet's room | Refused as not found | `BookingNotFound` |
| Uncovered | booking's window not covered by tablet periods | `check_in = "untracked"`, no button, POST refused | `InvalidBooking` |

</frozen-after-approval>

## Code Map

- `migrations/versions/0003_bookings.py` -- triggers `bookings_no_overlap_*` (L78–82) fire only on `UPDATE OF room_id, start_at, end_at`, so a check-in UPDATE is safe; don't touch them.
- `migrations/versions/0004_people_feed_token.py` -- pattern for a plain `op.add_column` migration; new `0005_door_tablets.py` follows it (`revision="0005"`, `down_revision="0004"`).
- `roombooker/core/identity.py` -- `COOKIE_NAME`, `COOKIE_MAX_AGE` (L20–21), `remember_person`/`_forget_person` (L70–90) are the cookie pattern to mirror for `door_tablet`; add `current_tablet` + `CurrentTablet`.
- `roombooker/core/time.py` -- `utc_now` L15, `to_text`/`from_text` L20/29, `uk_now` L33, `uk_midnight` L72; today's UK bounds = `uk_midnight(d)`..`uk_midnight(d + 1 day)`; Jinja filter `clock` L91.
- `roombooker/bookings/store.py` -- `bookings` Table L16–25 (add two columns), `begin_immediate` L35–42, `get` L83; add `in_room(room_id, start, end)` and `set_checked_in(id, at)`.
- `roombooker/bookings/service.py` -- `log` L25; error classes L49–61; `BookingView` L66–82 (new fields need defaults: `tests/test_ical.py` L13–28 builds it directly); `_views` L151–188 (needs `viewer: Person | None` for the door: no attendees, `can_cancel=False`); `cancel` L364 is the begin_immediate pattern.
- `roombooker/rooms/store.py`, `service.py` -- Table L15–23; `_require_manager` L75; `get_room` L157 is the manager-scoped lookup to reuse.
- `roombooker/rooms/web.py` -- `confirm_close`/`close_room` L202–217 and `_row_done` L84 are the in-row confirm pattern; `_page(confirming_id=…)` L46 the full-page fallback.
- `roombooker/templates/rooms/_row.html`, `_confirm_close_row.html`, `_table.html`, `_edit_row.html` -- `colspan="4"` must follow any new column.
- `roombooker/templates/base.html` -- has top bar and app-name link; the door page must not extend it.
- `tests/conftest.py` (`client`, alembic `upgrade head`), `tests/test_bookings.py` `act` L42 and `insert_booking` L323, `tests/test_rooms.py` L164 -- fixtures and patterns; patch `roombooker.core.time.utc_now` with `monkeypatch`.

## Tasks & Acceptance

**Execution:**
- [ ] `migrations/versions/0005_door_tablets.py` -- create `room_tablets` (id, room_id FK rooms, token unique, set_up_by FK people, set_up_at, removed_at) with partial unique index on `room_id WHERE removed_at IS NULL`; `op.add_column` `checked_in_at`; `op.execute("ALTER TABLE bookings ADD COLUMN freed_at VARCHAR CHECK (checked_in_at IS NULL OR freed_at IS NULL)")`; downgrade drops `freed_at`, then `checked_in_at`, then the table, with plain SQL -- AD-3 schema without rebuilding `bookings`.
- [ ] `roombooker/rooms/store.py`, `roombooker/rooms/service.py` -- `room_tablets` Table and queries; `set_up_tablet(actor, room_id) -> token` (replaces active one in one commit), `remove_tablet(actor, room_id)`, `tablet_room(token) -> Room | None`, `tablet_periods(room_ids) -> {room_id: [(set_up_at, removed_at|None)]}`, active tablet's `set_up_at` on `Room` for the row; logs -- AD-8.
- [ ] `roombooker/core/identity.py` -- `TABLET_COOKIE = "door_tablet"`, `remember_tablet`, `current_tablet` (resolves via `rooms.service.tablet_room`, else `None`), `CurrentTablet` -- AD-8.
- [ ] `roombooker/rooms/web.py` + `templates/rooms/` -- "Door tablet" column ("Since 13 Nov" / "None"); "Set up door tablet" and "Remove tablet" in-row confirms (setup confirm names the room, says the browser becomes its door tablet and is signed out, and gives "Mount it with the screen centre about 120 cm from the floor and set it never to sleep."); setup POST is a plain form that sets the tablet cookie, clears `person_id` and 303s to `/door`; remove follows `_row_done` -- R1, R9, R10.
- [ ] `roombooker/bookings/store.py`, `roombooker/bookings/service.py` -- columns, `in_room`, `set_checked_in`; `BookingView` gains `check_in` (`untracked|awaiting|checked_in|freed`), `check_in_opens_at`, `freed_at`, `can_check_in`, all defaulted; coverage = tablet periods (active one open-ended) cover `[start − 5, start + 15)`; `door_bookings(room)` for today; `check_in(room, booking_id)` per the matrix -- AD-2, AD-6, AD-7.
- [ ] `roombooker/bookings/web.py` + `templates/bookings/door.html` -- `GET /door` (room name, today's bookings with times, title, current or next marked, Check in button when `can_check_in`, "✓ Checked in"; or the not-set-up text), standalone page with `lang="en-GB"`, title "{Room} · Room Booking", app stylesheets, no links; `POST /door/check-in/{booking_id}` 303 to `/door`, refusals re-render the door page with the message -- AD-9.
- [ ] `tests/test_door.py` -- every matrix row; window boundaries at start − 6, start − 5, start + 15 − 1 min and start + 15 with `utc_now` patched; setup clears `person_id`; replace leaves one active tablet; migration upgrade/downgrade keeps the overlap triggers and attendees.

**Acceptance Criteria:**
- Given a manager in a private window, when they set up a room from Manage rooms, then they land on `/door` showing that room's bookings for today and Manage rooms in their main window shows "Since {date}" for it.
- Given the `/door` page, when it renders, then it contains no link and no element from the app's top bar.
- Given existing data, when migrating up and down, then `bookings_no_overlap_insert`, `bookings_no_overlap_update` and `booking_attendees` rows survive, and `uv run pytest --ignore=tests/e2e` passes.

## Implementation Notes

## Plan Change Log

## Review Triage Log

## Design Notes

Coverage, with periods sorted and the active one ending at +∞: walk from `start − 5`; each period starting at or before the cursor moves the cursor to its end; covered when the cursor reaches `start + 15`. Contiguous replacement (old `removed_at` = new `set_up_at`) keeps coverage unbroken.

Door refusals stay on the door: catch `DomainError` in the door POST and render `door.html` with the message and the error's status, never `errors/refused.html` (it carries the top bar).

## Verification

**Commands:**
- `uv run pytest --ignore=tests/e2e` -- expected: all pass, including `tests/test_door.py`.
- `uv run pytest tests/e2e` -- expected: existing suite still passes (Manage rooms table changed).

**Manual checks (if no CLI):**
- Run the app; in a private window, pick an office manager, set up a room, check in a booking in its window; in the main window, Remove the tablet and reload the private window to see the not-set-up page.
