---
title: 'My bookings: a day and week calendar of your bookings'
type: feature
ticket: ''
created: '2026-11-12'
status: built
baseline_revision: '2d594ea273897f1080a502a6f780ec3e5a4e06d6'
route: oneshot
route_source: pinned
risk: low
review: none
review_source: pinned
lenses_ran: []
review_loop_iteration: 0
context:
  - '{project-root}/_bmad-output/initiative-company-room-booking/architecture-company-room-booking/architecture-company-room-booking.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** People can book rooms, but the only place they see their bookings is the "Your upcoming bookings" list on Rooms. That list shows only bookings they organise, not ones they were invited to, and they can't look at a given day or week. This is loose work outside the initiative tree (user, 2026-11-12), built as asked rather than as `epic-my-calendar`.

**Approach:** Add a My bookings page with a day view and a week view of every booking the current person organises or attends. Today is highlighted. Each booking shows its room, time and title and links to its details page. On a phone the same bookings show as a list.

</frozen-after-approval>

## Implementation Notes

Oneshot route, pinned by the workflow. The work is read-only (no new table, no write path, no rule change), so risk is low. The architecture spine already names the module (`calendar`, web and service, no store, AD-1/AD-3) and the route (`/my-bookings`). Decisions:

- `bookings.store.for_person(session, person_id, start, end)` finds bookings that overlap `[start, end)` where the person is the organiser or in `booking_attendees`, in start order. `bookings.service.bookings_for_person(session, viewer, start_at, end_at)` returns them as `BookingView`s through `_views` (AD-3, AD-8). `calendar.service.my_bookings` is the only thing `calendar.web` calls, and it calls only `bookings.service` (AD-1).
- UK time stays in `core.time` (AD-5): `uk_midnight(day) -> UTC datetime` (UK midnight always exists, so day bounds are correct across clock changes) and `week_start(day)` (Monday). `calendar.web` builds the list of days (1 or 7), asks for the UTC range from the first day's midnight to the midnight after the last day, and puts each booking under every UK day it overlaps.
- Route `GET /my-bookings?view=day|week&date=YYYY-MM-DD`. A missing or bad `view` means `day`; a missing or bad `date` means today in the UK. Week view always runs Monday to Sunday and contains `date`. Controls are plain links (a full page load, AD-2): Day / Week toggle (`aria-current`), Previous / Next (moves by one day or one week), and Today.
- Today: its day heading reads "Today" plus the date, has the class `is-today` and `aria-current="date"`, and is navy-tinted. The tint always comes with the word "Today", so colour is never the only signal (DESIGN).
- Each booking is a link to `/bookings/{id}` showing its time `10:00–11:00`, title, room and office, and an "Organiser" or "Attending" label (EXPERIENCE "My bookings calendar"). Bookings that have ended are still shown.
- Layout is one HTML structure: a `<section>` per day, each with a heading and a `<ul>` of bookings. At 768px and wider, week view puts the seven days side by side as a CSS grid of columns. Below 768px the days stack as day-headed lists, the phone layout EXPERIENCE gives. Day view is a single list at every width.
- Empty states: "No bookings today." / "No bookings on Tue 17 Nov." for a day; "No bookings this week." / "No bookings in the week of Mon 16 Nov." for a week. In week view an empty day shows "Nothing booked".
- Top bar: a "My bookings" tab for everyone, placed between Rooms and Manage rooms (EXPERIENCE navigation). The details page keeps "Back to rooms"; changing details and cancel navigation is out of scope.
- Test policy: one test per distinct behaviour, and no test may repeat what another test already proves.

Tasks:
- `roombooker/core/time.py` -- add `uk_midnight`, `week_start`.
- `roombooker/bookings/store.py`, `service.py` -- add `for_person` / `bookings_for_person`.
- `roombooker/calendar/{__init__,service,web}.py`, `templates/calendar/my_bookings.html` -- the page; register the router in `app.py`.
- `templates/base.html` -- add the My bookings tab. `static/app.css` -- calendar styles.
- `tests/test_calendar.py` -- organised and attended bookings shown, other people's not; week runs Monday–Sunday and day bounds follow UK midnight; today is marked; a bad date or view falls back to today's day view; empty-state wording.
- `tests/e2e/test_my_bookings.py` -- at both widths: book for tomorrow, open My bookings, go to the week view, see today marked and the booking listed, open it and land on its details.
- `README.md` -- mention My bookings.

**Acceptance Criteria:**
- Given Hannah organises one booking and is an attendee of another, when she opens My bookings for that day, then both appear with room, time, title and "Organiser" / "Attending", and a booking she neither organises nor attends does not.
- Given any date, when the week view is shown, then it covers Monday to Sunday of that date's week, and Previous / Next move by exactly one week (one day in day view).
- Given today is in the view, when the page renders, then today's heading says "Today" and is marked `aria-current="date"`.
- Given a booking in the calendar, when it is clicked, then its details page opens.
- Given a 390px-wide screen, when the week view is shown, then the days are stacked lists, not side-by-side columns.

Built:
- New: `roombooker/calendar/{__init__,service,web}.py`, `templates/calendar/my_bookings.html`, `tests/test_calendar.py`, `tests/e2e/test_my_bookings.py`.
- Changed: `core/time.py` (`uk_midnight`, `week_start`), `bookings/store.py` (`for_person`: organiser OR an `IN` subquery on `booking_attendees`), `bookings/service.py` (`bookings_for_person`), `app.py` (router), `base.html` (My bookings tab for everyone), `app.css` (calendar styles; the page widens to 1120px only when a week is shown, via `.page:has(.calendar-week)`), README.
- Day view puts "Today, Thu 12 Nov" in the page's h2 (tinted, `aria-current="date"`) and has no per-day heading. Week view puts the same marking on that day's h3, and on a laptop tints the whole column.
- Every calendar booking uses DESIGN's "Mine" look (solid navy, white text): everything here is the viewer's own booking, and the Organiser / Attending word carries the distinction.
- Dates outside 1900–9000 fall back to today, so the date arithmetic can't overflow on a crafted URL.
- `tests/test_calendar.py` imports the booking tests' fixtures (`ids`, `act`, `room`, `book`) instead of copying them, with a file-level `noqa: F811`.
- Summer-time day bounds are tested on `uk_midnight` directly: bookings can only be made up to 90 days ahead, and from today (12 Nov) that window never reaches summer time.
- Not done: screenshots from a manually started server, because starting it needed approval. The e2e test checks the layout geometry at both widths instead (columns on a laptop, stacked on a phone). The repo has no formatter configured and existing files don't follow `ruff format`, so new files match the existing style; new files pass `ruff check`.
- Verification: `uv run pytest --ignore=tests/e2e` 93 passed; `uv run pytest tests/e2e` 19 passed.

## Plan Change Log

## Review Triage Log

## Verification

**Commands:**
- `uv run pytest --ignore=tests/e2e` -- expected: all pass, including `tests/test_calendar.py`
- `uv run pytest tests/e2e` -- expected: all pass at laptop and phone widths, including `test_my_bookings.py`
