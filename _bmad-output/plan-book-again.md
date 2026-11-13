---
title: 'Book again from a booking''s details page'
type: feature
ticket: ''
created: '2026-11-13'
status: built
baseline_revision: '62a55213e2c65abd164ea875bc23f304a85fcc48'
route: full
route_source: auto
risk: medium
review: quick
review_source: pinned
lenses_ran: [quick]
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Repeating a meeting means searching rooms and re-entering the title and attendees by hand.

**Approach:** A "Book again" link on the booking details page opens the existing booking form already filled with the same room, UK start clock time, length, title and attendees, on the date 7 days later. The form checks the slot when it loads. If the slot can't be booked, it says why and lets the person change the date, start and length without losing the title or attendees.

## Boundaries & Constraints

**Always:** Book again is a plain GET link to `/bookings/new` that works as a full page load. Booking still goes through `POST /bookings` → `bookings.service.book`, so the lock and the overlap triggers stay the guarantee. "One week later" means the UK date + 7 at the same UK clock time, converted only through `core.time`. Attendees are copied by id only when the viewer may see them (AD-8 visibility via `can_see_attendees`).

**Never:** No new tables or migrations. No writes on page load. Don't import `rooms`/`people` stores or services into `bookings/web.py`. Don't use `datetime.now()`. No recurring or series bookings.

**Decisions:**
- Only the organiser sees Book again, so the attendees always copy.
- Date/Start/Length pickers appear on the form only when the slot can't be booked. The normal form keeps its hidden time fields.
- Book again shows on bookings that have ended too. If one week later is still in the past, the form says so.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Free next week | Booking Tue 10:00–11:00, Room A, 2 attendees; Room A free next Tue | Form prefilled: Room A, next Tue 10:00, 1 h, same title, same attendees; Book creates the booking | No error expected |
| Slot taken | Room A already booked next Tue 10:00–10:30 | Form shows "Someone has already booked Room A at that time. Pick another time." and Date/Start/Length pickers; title and attendees kept | HTTP 200 on GET; checking a new time reloads the form via GET |
| Across a clock change | Booking 09:00 UK the week before clocks change | Prefilled 09:00 UK next week (the UTC hour differs) | No error expected |
| Time no longer valid | One week later is in the past, more than 90 days ahead, or skipped by the clocks | Form shows the existing reason (IN_THE_PAST / TOO_FAR_AHEAD / SKIPPED_TIME) and the pickers | Existing messages |
| Room closed | Room closed since | Form says the room is closed; Book is refused as today | Existing RoomClosed message |
| Attendee left | A copied attendee is no longer active | Dropped from the form (as `attendee_choices` already does) | No error expected |
| Normal booking form | Reached from Find rooms, slot free | Unchanged: hidden time fields, no pickers | No error expected |

</frozen-after-approval>

## Code Map

- `roombooker/bookings/web.py` -- `booking_details` renders details; `_form_page` builds the form context (reuse for the slot check); `new_booking` GET reloads the form; `_slot` parses UK text → UTC; `START_OPTIONS`/`LENGTH_OPTIONS` hold the picker values.
- `roombooker/bookings/service.py` -- `BookingView` (has attendee names, not ids); `_views` computes visibility; `check_slot`; `book` builds the conflict/closed messages (reuse the wording); `room_to_book`.
- `roombooker/bookings/store.py` -- `overlapping(start, end)` returns rows in any room; filter by `room_id` in the service. Don't add queries that write.
- `roombooker/core/time.py` -- `uk_to_utc`, `UK`; add a helper here if a UTC → (UK date, clock) split is needed.
- `roombooker/templates/bookings/details.html` -- add the link next to the Cancel action area.
- `roombooker/templates/bookings/new.html` -- hidden `date`/`start`/`length` inputs; the "search" submit pattern (`formaction="/bookings/new" formmethod="get"`) to reuse for a "Check time" button.
- `roombooker/templates/bookings/rooms.html` lines 9–24 -- Date/Start/Length picker markup to copy (with different ids).
- `tests/test_bookings.py` -- fixtures `room`, `book`, `act`, `ids`, `ANNOUNCE`, `uk_day`.

## Tasks & Acceptance

**Execution:**
- [x] `roombooker/bookings/service.py` -- add `attendee_ids: tuple[int, ...]` to `BookingView` (empty unless visible); add `slot_problem(session, room_id, start_at, length) -> str | None` that runs `check_slot` and reports a closed room or an overlapping booking in that room with the same wording as `book` -- the web layer can't query bookings itself
- [x] `roombooker/core/time.py` -- add `utc_to_uk(moment) -> (date, "HH:MM")` if needed -- the UK↔UTC conversion stays here
- [x] `roombooker/bookings/web.py` -- build the Book again query in `booking_details` (room, date+7, start, length, title, attendee_id…); in `_form_page`, call `slot_problem` when the slot parses and pass `pick_time=True` with START/LENGTH options whenever the slot has a problem
- [x] `roombooker/templates/bookings/details.html` -- "Book again" link, shown only when the viewer is the organiser (ended or not), not while confirming a cancel
- [x] `roombooker/templates/bookings/new.html` -- when `pick_time`, show Date/Start/Length pickers and a "Check time" GET submit in place of the hidden time inputs
- [x] `tests/test_bookings.py` -- one test per matrix row, plus a details-page link test
- [x] `tests/e2e/test_book_a_room.py` -- one flow: details → Book again → taken → pick another time → booked

**Acceptance Criteria:**
- Given a booking's details page, when the person clicks Book again and then Book without changing anything (slot free), then a new booking exists for next week and the original booking is untouched.
- Given the pickers are showing, when the person picks a free time and presses Check time, then the error goes away, the title and attendees are kept, and Book succeeds.

## Implementation Notes

- The Code Map was wrong that `attendee_choices` already drops inactive attendees: `people_service.names` includes inactive people. `attendee_choices` now filters with `get_active_person`, which affects the normal form too. An attendee who has left disappears when the form reloads, instead of Book failing with ATTENDEE_GONE.
- Added `core.time.utc_to_uk`, and `slot_problem` in the service. `book` and `slot_problem` share the closed/taken message builders.
- When the form's own check finds a problem, it shows the Date/Start/Length pickers. That includes a closed room, where changing the time can't help.
- Past, too-far-ahead and skipped times still return 422 on GET, as before. Only a taken slot or closed room stays 200.
- The tests write past and far-ahead bookings straight to SQLite, because `book` refuses those times. Existing tests also write to the DB directly.
- Review fix: a POST conflict or closed refusal now goes through the form's own re-check. That re-check's message ("Pick another time.") replaces the POST message, and the POST message is used only if the re-check finds nothing. A non-time POST error, such as an empty title, is announced together with any slot problem.

## Plan Change Log

## Review Triage Log

Pass 1 (quick): high 0, medium 1, low 5, false 0, maybe-false 0.

| # | Finding | Verdict | Route | Evidence / action |
|---|---------|---------|-------|-------------------|
| 1 | `_form_page`: a POST with a title or attendee error on a taken slot shows the pickers but doesn't say the slot is taken | medium | patch | Confirmed: `error = error or problem` hid the problem. Fixed: both are announced, the slot message is not repeated, and there is a test for an empty title on a taken slot. The frozen wording "Pick another time." is kept. |
| 2 | `new.html`: `required` on the date blocks the Add/Remove/Search submits | low | patch | Real when the date is empty (pickers show on NEEDS_DATE). Fixed by deleting `required`. |
| 3 | Start/Length selects fall back to the first option for a value not in the list | low | reject | Needs a hand-edited URL, because Book again always produces values from the lists. The fix would add branches. |
| 4 | `attendee_choices` change widens behaviour and adds a query per attendee | low | reject | The matrix row asks for exactly this behaviour. N is the number of attendees, which is small. Noted in Implementation Notes. |
| 5 | Clock-change test checks only the link URL, not the rendered form | low | reject | The form renders the URL values unchanged, as the free-slot test covers. The date is beyond 90 days, so the form can't show a clean prefill anyway. |
| 6 | No test submits the prefilled form unchanged (AC 1) | low | reject | The free-slot test checks that the hidden fields equal the values it then POSTs. That is the same thing for a plain form. |

## Design Notes

A GET that only reports a taken slot returns 200, because htmx doesn't swap non-2xx responses and the attendee search on this form uses htmx. `POST /bookings` keeps returning 409 on a conflict. The load-time check is advisory: a race between loading the form and pressing Book is still caught by the trigger.

## Verification

**Commands:**
- `uv run pytest --ignore=tests/e2e` -- expected: all pass
- `uv run pytest tests/e2e/test_book_a_room.py` -- expected: all pass
- `uv run ruff check roombooker tests` -- expected: clean (if ruff is configured)

