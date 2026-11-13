---
title: 'Add to calendar downloads a booking as an .ics file'
type: feature
ticket: '1'
created: '2026-11-13'
status: done
baseline_revision: 'a35097328314f4ca3b390f28367491086b74275a'
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

**Problem:** Room bookings live only in the room booker, so people retype them into Outlook, Google Calendar or Apple Calendar.

**Approach:** A booking's details page offers "Add to calendar", a plain GET link that downloads that booking as a one-event standard iCalendar (.ics) file. It shows the title, start and end, the room and office as location, and the organiser. The formatting lives in one pure function that story 2's feed will reuse.

## Boundaries & Constraints

**Always:** Times are written in UTC (`YYYYMMDDTHHMMSSZ`), taken from the booking's stored UTC moments, so each app shows them at the correct UK time on both sides of a clock change, with no VTIMEZONE block. The file follows RFC 5545: CRLF line endings, lines folded at 75 octets without splitting a UTF-8 character, and `\`, `;`, `,` and newlines escaped in text. `METHOD:PUBLISH`, a stable `UID` per booking (`booking-<id>@roombooker`), and `DTSTAMP` from `core.time.utc_now()`. The response is `text/calendar; charset=utf-8` with `Content-Disposition: attachment; filename="booking-<id>.ics"`. Anyone who can open the details page can download the file, including for an ended booking. `bookings/web.py` calls only `bookings.service`.

**Never:** No attendees or ATTENDEE lines, so the file never sends invitations and never leaks AD-8-hidden names. No new tables or migrations, no writes, no per-app variants, no Microsoft or Google calls, no `datetime.now()`. Nothing in `calendar/` or `people/` changes in this story.

**Decisions:**
- The organiser appears only as `DESCRIPTION:Booked by <name>`, with no ORGANIZER line, so an import is never treated as an invitation and no email goes into the file.
- The plan stays whole despite its ~1,900 tokens (the user's call): it has one goal.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| GMT booking | Booking 10:00–11:00 UK on a winter date, Snug, London, by Hannah Okafor | One VEVENT: `DTSTART:…T100000Z`, `DTEND:…T110000Z`, SUMMARY = title, LOCATION `Snug\, London`, organiser shown | No error expected |
| BST booking | Booking 10:00–11:00 UK on a summer date (written straight to SQLite, since `book` refuses past times) | `DTSTART:…T090000Z`, `DTEND:…T100000Z` | No error expected |
| Awkward text | Title with `,` `;` `\`, non-ASCII name, ~100 chars | Escaped; every physical line ≤ 75 octets; unfolding gives the original text back | No error expected |
| Someone else's booking | Viewer neither organiser nor attendee | Link shown; download works; no attendee names in the file | No error expected |
| Unknown or cancelled id | `/bookings/999/calendar.ics` | 404 with the existing "does not exist" message | Existing `BookingNotFound` |
| No cookie | Fresh browser | Pick your name, then back to the download (existing `CurrentPerson` flow) | Existing redirect |

</frozen-after-approval>

## Code Map

- `roombooker/bookings/web.py` -- `booking_details` (line ~246) renders details; add the download route beside it on `GET/HEAD /bookings/{booking_id:int}/calendar.ics`. `confirm_cancel` renders the same template: keep the link hidden while confirming.
- `roombooker/bookings/service.py` -- `get_booking(session, viewer, id) -> BookingView` (has `room.name`, `office_name`, `start_at`/`end_at` aware UTC, `title`, `organiser_name`, `organiser_id`). Add `booking_calendar(session, viewer, id) -> str`, which wraps `get_booking` and the formatter. Raises `BookingNotFound` for a bad id.
- New `roombooker/bookings/ical.py` -- pure, no DB: `calendar(events: Iterable[BookingView], stamp: datetime) -> str`. Imported only by `bookings.service` (store/service layering). Story 2 calls it through a service function for many events.
- `roombooker/core/time.py` -- add `ical_utc(moment) -> "YYYYMMDDTHHMMSSZ"` here (UTC formatting stays in `core.time`).
- `roombooker/templates/bookings/details.html` -- the `form-actions` block (lines 30–35) holds Book again and Cancel; add the Add to calendar link there and change the outer condition so it shows for everyone when not confirming.
- `roombooker/core/errors.py` -- `domain_error_handler` already turns `BookingNotFound` into a 404 page; nothing to change.
- `tests/test_bookings.py` -- fixtures `room`, `book`, `act`, `ids`, `insert_booking`, `booking_id`, `uk_day`. Bookings must start within 90 days, so the GMT case can use `book` on a late-November `uk_day`, and the BST case uses `insert_booking` with a past July date.

## Tasks & Acceptance

**Execution:**
- [x] `roombooker/core/time.py` -- add `ical_utc` -- UTC text formats live here
- [x] `roombooker/bookings/ical.py` -- escape, fold and emit VCALENDAR/VEVENT (VERSION, PRODID `-//Room booker//EN`, CALSCALE, METHOD:PUBLISH; UID, DTSTAMP, DTSTART, DTEND, SUMMARY, LOCATION, DESCRIPTION `Booked by <name>`, STATUS:CONFIRMED) -- the one formatter story 2 reuses
- [x] `roombooker/bookings/service.py` -- `booking_calendar` -- web calls only its service
- [x] `roombooker/bookings/web.py` -- download route returning the calendar text with the headers above
- [x] `roombooker/templates/bookings/details.html` -- "Add to calendar" link to `/bookings/{id}/calendar.ics`, shown to every viewer except while confirming a cancel
- [x] `tests/test_ical.py` -- pure formatter tests: escaping, folding (including a multi-byte character at the fold), CRLF, UTC times
- [x] `tests/test_bookings.py` -- one test per matrix row through the HTTP client, plus the link's visibility

**Acceptance Criteria:**
- Given any booking's details page, when the person clicks Add to calendar, then the browser downloads `booking-<id>.ics` holding exactly one VEVENT whose times, title, location and organiser match the page.
- Given the downloaded file, when it is opened in Outlook, Google Calendar and Apple Calendar, then each adds one event at the right UK time (a manual check by a person, `hitl`).

## Implementation Notes

- The GMT test writes its booking straight to SQLite (12 Jan 2027) instead of using `book` on a late-November `uk_day`, so it stays a GMT date whenever the suite runs; the other matrix rows go through `book`.
- The link carries the HTML `download` attribute as well as the server's `Content-Disposition: attachment`.
- `uv run pytest --ignore=tests/e2e`: 119 passed; `uv run pytest tests/e2e`: 21 passed. The Outlook / Google / Apple import check (`hitl`) is still to do.

## Plan Change Log

## Review Triage Log

Pass 1 (quick): high 0, medium 0, low 1, false 1, maybe-false 0.

| # | Finding | Verdict | Route | Evidence / action |
|---|---------|---------|-------|-------------------|
| 1 | AC 2 (import into Outlook, Google, Apple) is not met yet | false | reject | Not a code defect. AC 2 is the planned `hitl` check by a person, raised at sign-off; nothing in the diff can satisfy it. |
| 2 | `ical.escape` passes C0 controls and DEL into TEXT values, against RFC 5545 | low | patch | Confirmed reachable: room names only get `strip()` (`rooms/service.py`), and `_clean_title` keeps controls that aren't whitespace. Unlikely in everyday use, but the fix is a one-line filter, and one bad name would break story 2's whole feed. Fixed in `escape()` (HTAB kept), with an assertion in `tests/test_ical.py`. Both suites pass again: 119 and 21. |

## Design Notes

UTC instead of `TZID=Europe/London`: all three apps convert `Z` times to the viewer's zone, and leaving out VTIMEZONE removes the most common cause of Outlook import failures. The UID uses the booking id. Bookings have no AUTOINCREMENT, so SQLite can reuse the highest id after a delete. That doesn't matter for a one-off file, but story 2's feed should keep it in mind.

## Verification

**Commands:**
- `uv run pytest --ignore=tests/e2e` -- expected: all pass
- `uv run pytest tests/e2e` -- expected: all pass (details page still renders)

**Manual checks (if no CLI):**
- Download one GMT and one BST booking and import each into Outlook, Google Calendar and Apple Calendar: one event each, at the UK time the details page shows.
