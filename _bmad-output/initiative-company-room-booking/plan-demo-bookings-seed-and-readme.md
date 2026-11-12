---
title: 'Demo bookings in the seed, and a README for booking, My bookings and tests'
type: chore
ticket: ''
created: '2026-11-12'
status: built
baseline_revision: '5152d05d2331daa7ac750127d4cd88491bfd60a7'
route: oneshot
route_source: pinned
risk: low
review: none
review_source: pinned
lenses_ran: []
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** After a first local run there are no rooms and no bookings, so Rooms, a booking and My bookings look empty until someone builds data by hand; the README says little about booking, My bookings, demo data or the test suites.

**Approach:** The seed command gains an opt-in `--demo-bookings` flag that, after loading people, adds a few demo rooms per office and a realistic spread of bookings on the weekdays of this week and next (Monday this week to Friday next week, UK time, from the day it runs), organised by and inviting build-seed people. Then rewrite the README sections for booking, My bookings, demo bookings and tests.

## Boundaries & Constraints

**Always:** Rooms are written through `rooms.service.add_room` (as that office's manager) and bookings through `bookings.service` (AD-3), so the overlap/closed-room triggers still guard every row. Reruns are safe: existing demo rooms (same name, any case) are reused and a demo booking whose slot is already taken is skipped and counted. Demo bookings keep every booking rule except "not in the past", so earlier days of this week are filled too.

**Never:** No demo data without the flag (HR's list loads with the same command in production). No schema change or migration. No new dependencies. Not part of the initiative's ticket tree.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Plain seed | `seed build-people.csv` | People loaded; no rooms or bookings added | — |
| Demo load | `seed build-people.csv --demo-bookings` on an empty DB | Rooms in all 3 offices; bookings in all 3 offices on weekdays from Monday this week to Friday next week; every organiser and attendee is a build-seed person; exit 0, log counts | — |
| Rerun | same command again | No new rooms or bookings; log says how many were skipped | exit 0 |
| Not the build seed | `--demo-bookings` with a CSV lacking a demo person | Nothing demo is written | exit 1, `error: demo bookings need the build seed: <email> is not an active person` |

</frozen-after-approval>

## Code Map

- `roombooker/seed.py` -- CLI; people load in one transaction; add the flag and call the demo loader after
- `roombooker/bookings/service.py` -- `check_slot` (past/90-day window), `book` (trigger→`BookingConflict`/`RoomClosed`)
- `roombooker/rooms/service.py` -- `add_room(session, actor, name, capacity:str)`, `list_rooms(actor)`
- `roombooker/people/service.py`, `people/store.py` -- `Person`; no lookup by email yet
- `roombooker/core/time.py` -- `uk_now`, `week_start`, `uk_to_utc`
- `tests/conftest.py` -- `db_path`, `load_csv`; tests use the real clock
- `tests/e2e/conftest.py` -- seeds without the flag; leave as is

## Tasks & Acceptance

**Execution:**
- [ ] `roombooker/people/store.py`, `roombooker/people/service.py` -- add `active_people_by_email(session) -> dict[str, Person]` -- the demo loader names people by email
- [ ] `roombooker/bookings/service.py` -- `book(..., allow_past=False)`: when true, skip only the "in the past" check -- past-dated demo bookings through the one writer
- [ ] `roombooker/demo.py` -- new: demo rooms per office (name, capacity) and bookings as (week 0/1, weekday, UK start, minutes, office, room, title, organiser email, attendee emails), daily stand-ups per office plus one-offs, some cross-office; `load_demo(session) -> DemoResult` (rooms added/kept, bookings added/skipped); raise on a missing person before writing anything
- [ ] `roombooker/seed.py` -- `--demo-bookings` flag; on a demo error print `error: ...`, exit 1; log demo counts
- [ ] `tests/test_demo.py` -- one test per matrix row (plain/demo may share one test: plain load asserts no bookings, then the flag); no test may repeat what another already proves
- [ ] `README.md` -- first run uses `--demo-bookings`; sections: Booking a room, My bookings, Demo bookings (what, which weeks, rerun, not for production), Tests (all, without browser, one file, `-k`, headed)

**Acceptance Criteria:**
- Given a fresh database, when the README first-run commands run, then a seeded person (e.g. Hannah Okafor) sees demo bookings in My bookings for this week and next.
- Given the README, when a new developer follows it, then they can book, open My bookings, load demo bookings and run both test suites without reading code.

## Implementation Notes

Oneshot: a small, self-contained chore (seed data plus docs) with an obvious shape. Scope check: the README update documents the demo bookings, and the user asked for both together, so they stay one change.

- Opt-in flag, not always-on: the seed command also loads HR's list in production (AD-9), where fake bookings must never appear.
- `book(..., allow_past=True)` lifts only the past check, so Monday-to-today of this week is filled through the one writer; the triggers still guard overlaps and closed rooms.
- `roombooker/demo.py` pre-checks each slot with `bookings_in_slot` so a rerun skips quietly instead of logging 58 "refused" lines; `BookingConflict`/`RoomClosed` stay caught as a backstop. Not one transaction (`add_room`/`book` commit themselves); reruns are idempotent, so a partial load is fixed by running again.
- Every person is checked before any write; a non-build CSV loads people, then exits 1 with no demo data.
- Added `people.service.active_people_by_email` (+ `store.all_active`).
- Real CLI run twice on a throwaway DB: 10 rooms and 58 bookings (London 21, Manchester 19, Leeds 18), all 30 people in at least one; rerun added 0 and logged no refusals.
- Tests: `tests/test_demo.py` (3). Full suite 115 passed, e2e included.

## Plan Change Log

## Review Triage Log

## Verification

**Commands:**
- `uv run pytest --ignore=tests/e2e` -- expected: all pass
- `uv run pytest tests/e2e` -- expected: all pass
- fresh DB in scratch: `ROOMBOOKER_DB_PATH=<scratch>/demo.db uv run alembic upgrade head && ... seed seeds/build-people.csv --demo-bookings` twice -- expected: exit 0, second run adds nothing
