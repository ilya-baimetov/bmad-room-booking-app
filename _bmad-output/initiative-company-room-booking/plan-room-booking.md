---
title: 'Find a free room and book it'
type: feature
ticket: ''
created: '2026-11-12'
status: built
baseline_revision: '793248c70217ea85cf4debd2431405212d3d1216'
route: oneshot
route_source: pinned
risk: high
review: none
review_source: pinned
lenses_ran: []
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/initiative-company-room-booking/architecture-company-room-booking/architecture-company-room-booking.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** People can pick their name and office managers can manage rooms, but nobody can book a room. This is loose work outside the initiative tree (user, 2026-11-12), built exactly as asked rather than as `epic-find-and-book`.

**Approach:** Add a `bookings` module (web, service, store) and a migration for `bookings` and `booking_attendees`. In it, a Rooms page lists the free rooms for a chosen date, start time and length, with your own office first and a minimum-capacity filter. You book from the list with a title and attendees picked from the people list. A booking details page shows room, time, title and organiser to anyone, shows attendees only to the organiser, the attendees and the room's office managers, and lets the organiser cancel. Overlapping bookings, bookings of closed rooms, bookings in the past and bookings more than 90 days ahead are refused, even when two people book the same slot at once. Closing a room deletes its future bookings.

</frozen-after-approval>

## Implementation Notes

Oneshot route, pinned by the workflow. The user settled every scope question at the step-01 checkpoint (commit pending files, branch `room-booking`, build what was asked, attendees per AD-8). The architecture spine (AD-1 to AD-13) already fixes the module shape, so most of the remaining decisions are written down here:

- Layout follows the spine: `roombooker/bookings/{store,service,web}.py`, `roombooker/core/time.py` (the only Europe/London conversion, plus Jinja filters `14:00` and `Tue 17 Nov`), templates under `templates/bookings/`, migration `0003_bookings.py`.
- AD-4: `BEFORE INSERT/UPDATE` triggers on `bookings` refuse overlaps (half-open) and closed rooms with `RAISE(ABORT, 'booking_conflict' | 'room_closed')`. Writes run under `BEGIN IMMEDIATE`, and the service maps each abort to `BookingConflict`/`RoomClosed` (409). `CHECK (end_at > start_at)`. `booking_attendees` cascades on delete (AD-13). A threaded concurrency test proves the trigger.
- AD-5: UTC text `YYYY-MM-DDTHH:MM:00Z`. The service checks 15-minute alignment, a length of 15 to 240 minutes, a start no earlier than now and no more than 90 days after now, and a title of 1 to 100 characters. Attendees must be active people; the organiser is never stored as an attendee. Clock times that don't exist in the UK (the spring-forward gap) are refused in the web layer.
- Closing cascades: AD-1 forbids `rooms.service` → `bookings`. An `AFTER UPDATE OF is_closed` trigger on `rooms` deletes bookings whose `start_at` is later than now. It runs in the close transaction, and a booking already in progress stays. The close confirmation says future bookings will be cancelled. This is recorded as an ADR in `docs/decisions/`.
- Rooms page `/rooms`: the search form is a full GET that also works with htmx. It shows free open rooms grouped by office (own office first, then by name), each with a Book link, and lists "Booked at this time" (title, organiser, link to details) and "Your upcoming bookings" so the organiser can reach Cancel. `/` sends non-managers to `/rooms`, and the top bar gains a Rooms tab for everyone.
- Booking form `/bookings/new?room&date&start&length`: the title defaults to "{Name}'s meeting". Attendees are added by htmx type-ahead from `people.service.search_active_people`, held as hidden `attendee_id` inputs; without JS a GET search reloads the form. A refusal keeps the title and attendees. `POST /bookings` redirects to `/bookings/{id}`, and `POST /bookings/{id}/cancel` asks for confirmation first (GET `/bookings/{id}/cancel`).
- Test policy: one test per distinct behaviour, and no test repeats what another already proves.

Built:
- New: `migrations/versions/0003_bookings.py`, `roombooker/core/time.py`, `roombooker/bookings/{store,service,web}.py`, `templates/bookings/{rooms,new,details,_item}.html`, `docs/decisions/adr-closing-a-room-deletes-its-future-bookings.md`, `tests/test_bookings.py`, `tests/e2e/test_book_a_room.py`.
- Changed: `people.service`/`store` (`names`, which includes inactive people, and `office_names`); `rooms.service`/`store` (`all_rooms`, `find_room`); `app.py` (router, `clock`/`day` filters); `/` now sends non-managers to `/rooms` (`people/landing.html` removed); top bar has a Rooms tab for everyone; close confirmation mentions cancelled bookings; README; CSS.
- Existing tests updated for the new landing, the tab bar and the close wording.
- `bookings.web` reaches rooms and people only through `bookings.service` (`room_to_book`, `attendee_choices`), per AD-1.
- `BEGIN IMMEDIATE` works because Python's sqlite3 in legacy transaction mode opens no transaction for reads. `store.begin_immediate` commits the session, then issues it. A scratch check confirmed a second connection is locked out until rollback.
- The 90-day limit is measured from now (start ≤ now + 90 days), not by UK calendar date. Cancelling a booking that has already ended is refused. Managers cancel only their own bookings (as asked), not others' in their office.
- One full-suite run of seven had a single failure that never reproduced. Six later full runs passed, and the failure's name was not captured. Treat it as a possible flaky test.

## Plan Change Log

## Review Triage Log

## Verification

**Commands:**
- `uv run pytest --ignore=tests/e2e` -- expected: all pass, including new booking tests and the concurrency test
- `uv run pytest tests/e2e` -- expected: all pass at laptop and phone widths, including a find-book-cancel flow
