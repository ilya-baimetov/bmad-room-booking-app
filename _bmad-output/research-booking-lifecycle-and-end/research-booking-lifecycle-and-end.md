---
title: 'Codebase research: booking lifecycle and end'
type: codebase
ask: |-
  before we add check-in, how do bookings end today, and what depends on that?
repository: '/home/claude/runs/inherited'
commit: '9184f9df73e5814b9fa6eeded775adb5722ab308'
branch: 'my-changes'
status: complete
validation: 'normal'
claims: {disputed: 2, overturned: 1, verified: 18}
created: '2026-11-13'
updated: '2026-11-13'
---

# Codebase research: booking lifecycle and end

This document describes how bookings end in room-booker at commit `9184f9d`, and what reads or depends on how they end. It is for whoever plans the next change and for anyone checking a single claim. Every claim cites a line or a commit. It recommends nothing.

In short, a booking ends in one of three ways: its end time passes and nothing is written (question 1a); the organiser cancels and Python deletes the row (`roombooker/bookings/service.py:364-371 (cancel) @ 9184f9d`); or the room closes and a trigger deletes its bookings that have not started (`migrations/versions/0003_bookings.py:84-95 (upgrade) @ 9184f9d`). No column records an end state (`roombooker/bookings/store.py:16-25 (bookings) @ 9184f9d`).

## Questions

1. (how) How does a booking stop being active today? What marks its end (end time, cancellation, deletion, anything else), and which code paths and database triggers produce each one?
2. (what touches) What reads a booking's end time, or depends on a booking existing or being removed? This covers listings, calendar views, the iCal download and feed, overlap checks, room closing, and seed/demo data.
3. (how) How do the overlap triggers (`migrations/versions/0003_bookings.py`) and the trigger `rooms_close_cancels_future_bookings` decide which bookings count, for example past or future, and current or removed?
4. (why) Why is the end of a booking represented the way it is, for example as a delete rather than a recorded state?
5. (how) How are a booking's lifecycle, its end, and its removal tested?

Researchers ran as fresh subagents given only these questions. They were Claude Code subagent types, which may load the repository's `AGENTS.md`; nothing in that file names the work in progress.

## 1. How a booking stops being active

A booking has no status, cancelled, or soft-delete column. It is a row with `id`, `room_id`, `organiser_id`, `title`, `start_at` and `end_at`, the times stored as UTC text (`roombooker/bookings/store.py:16-25 (bookings) @ 9184f9d`). The schema adds `CheckConstraint("end_at > start_at")` (`migrations/versions/0003_bookings.py:54-56 (upgrade) @ 9184f9d`). A booking stops being active in one of three ways. Deactivating a person is not one of them.

**1a. Its end time passes. Nothing is written.** "Ended" is computed at read time by comparing `end_at` with `core.time.utc_now()`:

- The upcoming list filters on `end_at > after`, with `after = utc_now()` (`roombooker/bookings/store.py:54-63 (upcoming_for_organiser) @ 9184f9d`, `roombooker/bookings/service.py:200-205 (upcoming_bookings) @ 9184f9d`).
- The details page sets `has_ended = booking.end_at <= uk.utc_now()` (`roombooker/bookings/web.py:257 (booking_details) @ 9184f9d`). The template hides Cancel unless `booking.can_cancel and not has_ended` (`roombooker/templates/bookings/details.html:34 (content) @ 9184f9d`).
- The service refuses to cancel once `end_at <= utc_now()` and raises `InvalidBooking(ALREADY_ENDED)` (`roombooker/bookings/service.py:359-360 (booking_to_cancel) @ 9184f9d`; the message is at `roombooker/bookings/service.py:46 (ALREADY_ENDED) @ 9184f9d`).
- The feed includes only bookings that end later than 30 days ago (`roombooker/bookings/service.py:285-290 (feed_calendar) @ 9184f9d`).

Ended bookings stay in the table indefinitely. A search for `delete(` and `DELETE FROM` across `*.py` found no purge or expiry, only the two delete paths below.

**1b. The organiser cancels. Python deletes the row.**

- `GET /bookings/{id}/cancel`: `roombooker/bookings/web.py:299-314 (confirm_cancel) @ 9184f9d` calls `service.booking_to_cancel` and renders the confirm form (`roombooker/templates/bookings/details.html:22-29 (content) @ 9184f9d`).
- `POST /bookings/{id}/cancel`: `roombooker/bookings/web.py:317-322 (cancel) @ 9184f9d` redirects with 303 to `/rooms?notice=cancelled`.
  - `roombooker/bookings/service.py:364-371 (cancel) @ 9184f9d` (docstring: "Cancel (delete, AD-13)") runs these steps in order:
    1. `booking_to_cancel`
    2. `store.begin_immediate` (`roombooker/bookings/store.py:35-42 (begin_immediate) @ 9184f9d`)
    3. `store.delete_booking` (`roombooker/bookings/store.py:118-120 (delete_booking) @ 9184f9d`, which runs `DELETE FROM bookings WHERE id=…`)
    4. commit, then a log line

Checks on this path that reject a request:

- `_get_row` raises `BookingNotFound` (404, "It may have been cancelled") when the id is missing or out of range (`roombooker/bookings/service.py:267-271 (_get_row) @ 9184f9d`).
- A non-organiser gets `NotAllowed(ONLY_ORGANISER)` (`roombooker/bookings/service.py:356-358 (booking_to_cancel) @ 9184f9d`; `roombooker/bookings/service.py:93-95 (can_cancel_booking) @ 9184f9d`).
- An ended booking gets `InvalidBooking(ALREADY_ENDED)` (`roombooker/bookings/service.py:359-360 (booking_to_cancel) @ 9184f9d`). A booking that has started but not ended can still be cancelled.
- The ended check runs before `begin_immediate`, outside the write lock (`roombooker/bookings/service.py:366-367 (cancel) @ 9184f9d`).

Attendee rows go with the booking through `ON DELETE CASCADE` on `booking_attendees.booking_id` (`migrations/versions/0003_bookings.py:65-66 (upgrade) @ 9184f9d`). The cascade depends on `PRAGMA foreign_keys=ON`, which every connection sets (`roombooker/core/db.py:12-16 (PRAGMAS) @ 9184f9d`).

**1c. A manager closes the room. A database trigger deletes its bookings that have not started.**

- `roombooker/rooms/web.py:213-217 (close_room) @ 9184f9d` handles `POST /manage-rooms/{room_id}/close`, after a GET confirm page (`roombooker/rooms/web.py:202-210 (confirm_close) @ 9184f9d`).
  - `roombooker/rooms/service.py:215-218 (close_room) @ 9184f9d` calls `_set_closed(..., is_closed=True)` (`roombooker/rooms/service.py:205-212 (_set_closed) @ 9184f9d`). In `_set_closed`, `_require_manager` rejects anyone who does not manage the room's office.
    - `roombooker/rooms/store.py:49-50 (set_closed) @ 9184f9d` runs `UPDATE rooms SET is_closed=…`, on the column defined at `migrations/versions/0002_rooms.py:31 (upgrade) @ 9184f9d`.
      - The trigger `rooms_close_cancels_future_bookings` (`migrations/versions/0003_bookings.py:84-95 (upgrade) @ 9184f9d`) is `AFTER UPDATE OF is_closed ON rooms WHEN NEW.is_closed AND NOT OLD.is_closed`. It runs `DELETE FROM bookings WHERE room_id = NEW.id AND start_at > strftime('%Y-%m-%dT%H:%M:%SZ','now')`.

Python deletes nothing on this path; the `close_room` docstring points to the trigger (`roombooker/rooms/service.py:216-217 (close_room) @ 9184f9d`). The trigger reads SQLite's own `'now'`, whereas paths 1a and 1b read `core.time.utc_now()`, so the code has two separate clocks. Reopening a room does not restore the deleted bookings.

**Not an end path: deactivating a person.** `load_people` marks people missing from the CSV inactive, and its docstring says "Never deletes" (`roombooker/people/store.py:144-174 (load_people) @ 9184f9d`). There is no trigger on `people`. Bookings an inactive person organises or attends stay. The active flag only stops that person being added as an attendee later (`roombooker/bookings/service.py:322-323 (book) @ 9184f9d`).

Looked for at `9184f9d` and not found: any status, cancelled, or soft-delete column on bookings (a git grep for `status|cancelled_at|deleted_at|removed` in `roombooker` and `migrations` found only HTTP status codes, the iCal `STATUS:CONFIRMED` line and an unrelated variable); any Python `UPDATE` of bookings (the store has only `insert` and `delete_booking`); any booking delete in `seed.py` or `demo.py`.

## 2. What reads a booking's end time or depends on a booking existing

These are listed by layer. Each entry gives a call site and how it touches the end time or whether the booking exists.

**Schema and database**
- `migrations/versions/0003_bookings.py:54-56 (upgrade) @ 9184f9d`: `start_at` and `end_at` are NOT NULL strings, and CHECK `end_at > start_at` rejects a row whose end is not after its start.
- `migrations/versions/0003_bookings.py:58-59 (upgrade) @ 9184f9d`: the only indexes are `(room_id, start_at)` and `(organiser_id)`. No index contains `end_at`.
- `migrations/versions/0003_bookings.py:65-66 (upgrade) @ 9184f9d`: attendees cascade on booking delete.
- `migrations/versions/0003_bookings.py:23-34 (_GUARD) @ 9184f9d`: the overlap guard reads `start_at` and `end_at` of every booking in the room (see question 3).
- `migrations/versions/0003_bookings.py:84-95 (upgrade) @ 9184f9d`: the close trigger reads `start_at` only, never `end_at`.

**Store queries**
- `roombooker/bookings/store.py:45-51 (overlapping) @ 9184f9d`: any room where `start_at < :end AND end_at > :start`.
- `roombooker/bookings/store.py:54-63 (upcoming_for_organiser) @ 9184f9d`: `end_at > after`.
- `roombooker/bookings/store.py:66-80 (for_person) @ 9184f9d`: the same overlap test, limited to bookings the person organises or attends.
- `roombooker/bookings/store.py:83-84 (get) @ 9184f9d`: fetch by id. A missing row becomes `BookingNotFound` through `roombooker/bookings/service.py:267-271 (_get_row) @ 9184f9d`.
- `roombooker/bookings/store.py:118-120 (delete_booking) @ 9184f9d`: the only Python DELETE on bookings.

**Bookings service**
- `roombooker/bookings/service.py:107-120 (check_slot) @ 9184f9d`: computes the end as start plus length. It rejects a start off the quarter hour (`NOT_ON_QUARTER`), a length outside 15–240 minutes or not a multiple of 15 (`BAD_LENGTH`), a start before now unless `allow_past` (`IN_THE_PAST`), and a start more than 90 days ahead (`TOO_FAR_AHEAD`). It does not check the end against now.
- `roombooker/bookings/service.py:123-148 (free_rooms) @ 9184f9d`: the end comes from `check_slot`, then `store.overlapping` gives the taken rooms. Closed rooms are dropped in Python.
- `roombooker/bookings/service.py:151-188 (_views) @ 9184f9d`: parses `end_at` into `BookingView.end_at` and sets `can_cancel`. Every path that produces a view goes through here.
- `roombooker/bookings/service.py:191-197 (bookings_in_slot) @ 9184f9d`: end is start plus length, without `check_slot`, then `store.overlapping`.
- `roombooker/bookings/service.py:200-205 (upcoming_bookings) @ 9184f9d`: `upcoming_for_organiser(after=utc_now(), limit=20)`. A booking stays listed until its end passes.
- `roombooker/bookings/service.py:208-214 (bookings_for_person) @ 9184f9d`: `store.for_person` → `_views`.
- `roombooker/bookings/service.py:225-240 (slot_problem) @ 9184f9d`: an advisory check that the room is closed, then `check_slot`, then an overlap in this room.
- `roombooker/bookings/service.py:279-282 (booking_calendar) @ 9184f9d`: the single-booking `.ics`, with no ended or closed filter.
- `roombooker/bookings/service.py:285-290 (feed_calendar) @ 9184f9d`: bookings for the person that overlap the window from 30 days ago to `FEED_END` (`9999-12-31T23:59Z`).
- `roombooker/bookings/service.py:302-350 (book) @ 9184f9d`: the end comes from `check_slot`, then `begin_immediate` and insert. The trigger aborts map to `RoomClosed`/`BookingConflict` (see question 3).
- `roombooker/bookings/service.py:353-371 (booking_to_cancel, cancel) @ 9184f9d`: the ended check, then the delete (see question 1).

**iCal**
- `roombooker/bookings/ical.py:52-64 (uid) @ 9184f9d`: the UID hashes room, `start_at`, `end_at` and title, "so a booking id SQLite reuses after a delete is a new event". Changing the end time gives a new UID.
- `roombooker/bookings/ical.py:67-79 (_event) @ 9184f9d`: writes `DTEND` from `end_at` and always `STATUS:CONFIRMED`. Cancelled events are never written; they drop out of the feed.

**Calendar module**
- `roombooker/calendar/service.py:18-22 (my_bookings) @ 9184f9d`: passes through to `bookings_for_person`.
- `roombooker/calendar/service.py:25-31 (feed) @ 9184f9d`: looks up the token, then calls `feed_calendar`.
- `roombooker/calendar/web.py:67-121 (my_bookings) @ 9184f9d`: groups bookings by day with `b.start_at < bounds[i+1] and b.end_at > bounds[i]` (line 91), so a booking spanning midnight shows on both days.
- `roombooker/calendar/web.py:156-169 (feed) @ 9184f9d`: returns 404 for an unknown token, otherwise the feed text.

**Bookings web**
- `roombooker/bookings/web.py:76-78 (_slot_text) @ 9184f9d`: end is start plus length, shown as UK time.
- `roombooker/bookings/web.py:85-126 (rooms) @ 9184f9d`: calls `upcoming_bookings`, `free_rooms` and `bookings_in_slot`.
- `roombooker/bookings/web.py:129-178 (_form_page) @ 9184f9d`: calls `slot_problem`.
- `roombooker/bookings/web.py:246-267 (booking_details) @ 9184f9d`: shows `end_at`. `has_ended` gates the Cancel button.
- `roombooker/bookings/web.py:270-278 (booking_calendar) @ 9184f9d`: the `.ics` download.
- `roombooker/bookings/web.py:281-296 (_book_again_query) @ 9184f9d`: the length is `end_at - start_at`.
- `roombooker/bookings/web.py:299-322 (confirm_cancel, cancel) @ 9184f9d`: the cancel routes.

**Templates**
- `roombooker/templates/bookings/_item.html:4 (booking-when) @ 9184f9d`: renders `b.end_at`. It is used for "Booked then" (`roombooker/templates/bookings/rooms.html:58-63 (content) @ 9184f9d`) and "Your upcoming bookings" (`roombooker/templates/bookings/rooms.html:67-74 (content) @ 9184f9d`).
- `roombooker/templates/bookings/details.html:10 (content) @ 9184f9d`: renders the end time. Lines 32–34 hold Add to calendar, Book again, and Cancel when `can_cancel and not has_ended`.
- `roombooker/templates/calendar/my_bookings.html:35 (content) @ 9184f9d`: renders `end_at`. Lines 20–21 and 30–44 render the empty states.

**Rooms**
- `roombooker/rooms/service.py:205-219 (_set_closed, close_room) @ 9184f9d`: closes the room. The trigger does the delete.

**Seed and demo**
- `roombooker/demo.py:176-210 (load_demo) @ 9184f9d`: checks each slot with `bookings_in_slot` and skips it if taken or the room is closed. Otherwise it calls `book(..., allow_past=True)` and counts `BookingConflict`/`RoomClosed` as skipped.
- `roombooker/seed.py:141-157 (_load_demo) @ 9184f9d`: calls `demo.load_demo` behind `--demo-bookings`.

**Patterns that do the same thing in more than one place**
- **Overlap test, twice.** It is enforced in SQL per room (`migrations/versions/0003_bookings.py:23-34 (_GUARD) @ 9184f9d`) and read in SQLAlchemy across all rooms (`roombooker/bookings/store.py:45-51 (overlapping) @ 9184f9d`, `roombooker/bookings/store.py:66-80 (for_person) @ 9184f9d`).
- **"Has ended" check, twice.** Both `roombooker/bookings/service.py:359-360 (booking_to_cancel) @ 9184f9d` and `roombooker/bookings/web.py:257 (booking_details) @ 9184f9d` compare `end_at <= utc_now()`.
- **Closed-room check, in four places.** The trigger guard (`migrations/versions/0003_bookings.py:23-34 (_GUARD) @ 9184f9d`), `roombooker/bookings/service.py:123-148 (free_rooms) @ 9184f9d`, `roombooker/bookings/service.py:225-240 (slot_problem) @ 9184f9d`, and `roombooker/demo.py:176-210 (load_demo) @ 9184f9d`.

Looked for at `9184f9d` and not found: any reader of booking end times outside `bookings`, `calendar` and the templates above; any `end_at` in `roombooker/static/`; any bookings in `seeds/`.

## 3. Which bookings the triggers count

**Overlap guard.** Both `bookings_no_overlap_insert` (BEFORE INSERT) and `bookings_no_overlap_update` (BEFORE UPDATE OF `room_id, start_at, end_at`) run the same `_GUARD` body (`migrations/versions/0003_bookings.py:77-83 (upgrade) @ 9184f9d`). It makes two checks, in order:

1. If `rooms.is_closed` is true for `NEW.room_id`, it aborts with `room_closed` (`migrations/versions/0003_bookings.py:23-34 (_GUARD) @ 9184f9d`). This runs first, so a booking in a closed room reports `room_closed` even when it also overlaps.
2. If another booking in the same room satisfies `other.start_at < NEW.end_at AND NEW.start_at < other.end_at`, it aborts with `booking_conflict`. Intervals are half-open, so back-to-back bookings pass. `other.id IS NOT NEW.id` stops an update colliding with its own row.

The guard has no condition on time or status. It counts every row in the room, past, current and future, so a finished booking still blocks an overlapping new one. A booking stops counting only when it is deleted. Times compare as text, which works because they are stored as UTC `YYYY-MM-DDTHH:MM:00Z` (`migrations/versions/0003_bookings.py:54-56 (upgrade) @ 9184f9d`). No app code updates `bookings`, so the UPDATE trigger never fires from the app.

**How an abort reaches the user.** `roombooker/bookings/service.py:302-350 (book) @ 9184f9d` rolls back an `IntegrityError` and classifies it by a substring of its message. `room_closed` becomes `RoomClosed`, `booking_conflict` becomes `BookingConflict`, and anything else is re-raised. Before the insert, `check_slot` refuses past starts unless `allow_past`, which only demo data passes. So past bookings come from demo data or direct inserts, and the guard still counts them.

**Advisory duplicate.** `roombooker/bookings/service.py:225-240 (slot_problem) @ 9184f9d` runs the closed check and the same half-open overlap test through `store.overlapping`, filtered to the room in Python. It has no time or status filter either. Its docstring says the triggers remain the guarantee.

**Close trigger.** `migrations/versions/0003_bookings.py:84-95 (upgrade) @ 9184f9d` fires only when a room goes from open to closed (`WHEN NEW.is_closed AND NOT OLD.is_closed`), so reopening a room, or closing one that is already closed, deletes nothing. It deletes rows where `start_at > strftime('%Y-%m-%dT%H:%M:%SZ','now')`:

- Bookings in progress are kept. So are past bookings, and a booking whose `start_at` equals the current second, because the test is `>`.
- It never reads `end_at`.
- SQLite's `now` carries real seconds while stored values end in `:00Z`. The strings are the same length, so the text comparison holds.

The room-close ADR records the intended rule and the race between booking and closing. A booking that commits first is deleted by the trigger. One that commits after the close is refused by the guard with `room_closed` (`docs/decisions/adr-closing-a-room-deletes-its-future-bookings.md:3 (Closing a room deletes its future bookings, in a database trigger) @ 9184f9d`). The ADR also says the database clock means a fake clock in tests cannot move the trigger (`docs/decisions/adr-closing-a-room-deletes-its-future-bookings.md:7 (Closing a room deletes its future bookings, in a database trigger) @ 9184f9d`).

**"Removed" bookings.** There is no column for them (see question 1). Whether a booking is current or removed depends only on whether its row exists.

## 4. Why the end is represented this way

The history shows what the code does, but not why cancel was made a delete. Every cited line about cancelling and deleting arrives in one parentless commit:

- `roombooker/bookings/service.py:364-371 (cancel) @ 9184f9d`, `roombooker/bookings/store.py:118-120 (delete_booking) @ 9184f9d`, the cascade at `migrations/versions/0003_bookings.py:65-66 (upgrade) @ 9184f9d`, and the close trigger at `migrations/versions/0003_bookings.py:84-95 (upgrade) @ 9184f9d` all arrive in `5f72d52 "chore: remove BMad files and the walkthrough log"`.
- That commit's message calls it "the same app with no BMad install, planning documents or run log… The greenfield-done tag keeps them." This clone has no `greenfield-done` tag, so history stops there.

What the repository does record:

- The code cites "AD-13" for cancel as delete and says nothing more (`roombooker/bookings/service.py:364-371 (cancel) @ 9184f9d`, `roombooker/bookings/store.py:118-120 (delete_booking) @ 9184f9d`). AD-n points to a planning document that no longer exists (`AGENTS.md:29 (Conventions that differ from defaults) @ 9184f9d`).
- The room-close ADR says future bookings "are deleted (cancelled, as AD-13 defines cancelling)", following a user decision on 2026-11-12 that "closing a room cancels its future bookings" (`docs/decisions/adr-closing-a-room-deletes-its-future-bookings.md:3 (Closing a room deletes its future bookings, in a database trigger) @ 9184f9d`).
  - The delete sits in a trigger, not in `rooms.service`, because service dependencies run one way ("AD-1") and because a trigger wins the race described in question 3.
  - The ADR names the trade-offs it accepts:
    - a second writer of `bookings` (contrary to "AD-3")
    - "The cancelled bookings are not logged one by one: only the close is logged"
    - the database clock
    - the close confirmation not saying how many bookings it cancels
  - It gives two revisit conditions: "if retention (OQ-3) asks for cancelled bookings to be kept", or if a later epic decides to move the bookings to an open room instead (`docs/decisions/adr-closing-a-room-deletes-its-future-bookings.md:10 (Closing a room deletes its future bookings, in a database trigger) @ 9184f9d`). The first is the only text in the repository that mentions keeping cancelled bookings as an alternative, and it leaves that to an open question rather than rejecting it.
- Bookings are the only entity here with no recorded end state. Rooms record `is_closed` (`migrations/versions/0002_rooms.py:31 (upgrade) @ 9184f9d`), and people are marked inactive rather than deleted (`roombooker/people/store.py:144-174 (load_people) @ 9184f9d`).
- Later code adapts to the delete model and does not revisit it: calendar UIDs gained a content hash because SQLite can reuse a deleted booking's id (`d7c6ceb "feat(calendar): private calendar feed per person, with reset on My bookings"`; full history and citations under Decisions found).

No pull requests were found. Every cited commit is either `5f72d52` or a direct commit on the local branch.

## 5. How the lifecycle is tested

**Time in tests.**

- Nothing freezes or fakes the clock. `tests/test_bookings.py:1-4 (module docstring) @ 9184f9d` states the policy: times are relative to the real clock, because the close-room trigger uses SQLite's own "now".
- Python takes the current time from `datetime.now(UTC)` (`roombooker/core/time.py:15-17 (utc_now) @ 9184f9d`). That function's docstring says "Tests replace this to fix the clock", but no test does. The trigger takes it from SQLite (`migrations/versions/0003_bookings.py:84-95 (upgrade) @ 9184f9d`).
- Future dates come from the real UK date through `uk_day(n)` (`tests/test_bookings.py:32-33 (uk_day) @ 9184f9d`). The `book` fixture defaults to tomorrow at 10:00 for 60 minutes (`tests/test_bookings.py:68-86 (book) @ 9184f9d`).
- Past and far-future bookings are written straight into SQLite, "for times the web refuses" (`tests/test_bookings.py:323-335 (insert_booking) @ 9184f9d`). Fixed past dates such as 2020-01-07 stand in for ended bookings.
- The only fixed clock is a timestamp passed into the iCal formatter (`tests/test_ical.py:10 (STAMP) @ 9184f9d`).

**Harness.**

- Each test gets a temporary SQLite file migrated through Alembic (`tests/conftest.py:19-33 (migrate_to_head) @ 9184f9d`).
- Tests drive the app through `TestClient` (`tests/conftest.py:65-68 (client) @ 9184f9d`).
- e2e runs Alembic, the seed and uvicorn once per session (`tests/e2e/conftest.py:59-90 (live_server) @ 9184f9d`).

**Covered.**

- *Create:*
  - Refusals keep the form: overlap, past, too far ahead, off-quarter, bad length, blank title, and closed room (`tests/test_bookings.py:184-212 (test_refused_bookings_keep_the_form) @ 9184f9d`).
  - Two people booking the same slot at once, where exactly one gets `BookingConflict` (`tests/test_bookings.py:215-238 (test_two_people_booking_the_same_slot_at_once) @ 9184f9d`).
  - The database refusing raw overlapping inserts and updates and closed-room inserts (`tests/test_bookings.py:241-253 (test_database_refuses_overlaps_and_closed_rooms) @ 9184f9d`).
- *Cancel* (`tests/test_bookings.py:256-273 (test_only_the_organiser_cancels) @ 9184f9d`):
  - A non-organiser, even the office manager, gets 403.
  - The organiser confirms, then POSTs and gets a 303.
  - The booking and attendee rows are gone, details returns 404, and the slot can be booked again.
  - Side effects:
    - The cancelled booking leaves the feed (`tests/test_feed.py:113-119 (test_cancelled_booking_leaves_the_feed) @ 9184f9d`).
    - Its `.ics` returns 404 (`tests/test_bookings.py:566-572 (test_add_to_calendar_unknown_or_cancelled_booking_is_404) @ 9184f9d`).
    - A reused id gets a different UID (`tests/test_feed.py:240-250 (test_reused_booking_id_gets_a_different_uid) @ 9184f9d`).
  - e2e cancel through the browser (`tests/e2e/test_book_a_room.py:15-52 (test_find_book_and_cancel) @ 9184f9d`).
- *Close room* (`tests/test_bookings.py:276-291 (test_closing_a_room_cancels_its_future_bookings) @ 9184f9d`):
  - A 2020 booking survives, the future booking and its attendees are deleted, and the future booking returns 404.
  - Closing also removes the room's bookings from the feed (`tests/test_feed.py:122-131 (test_closing_a_room_removes_its_bookings_from_the_feed) @ 9184f9d`).
  - The close confirmation text is checked with no bookings present (`tests/test_rooms.py:164-191 (test_close_after_confirmation_then_reopen) @ 9184f9d`).
- *Ended bookings:*
  - Book again still shows (`tests/test_bookings.py:338-349 (test_book_again_link_only_for_the_organiser) @ 9184f9d`).
  - Book again when the time is no longer valid (`tests/test_bookings.py:432-452 (test_book_again_time_no_longer_valid) @ 9184f9d`).
  - Book again when the room has since closed (`tests/test_bookings.py:455-466 (test_book_again_room_closed) @ 9184f9d`).
  - The feed keeps bookings that ended 29 days ago and drops those that ended 31 days ago (`tests/test_feed.py:68-92 (test_subscribed_feed_has_organised_and_attended_bookings_only) @ 9184f9d`).
- *Demo:* fills this week and next (`tests/test_demo.py:39-52 (test_demo_bookings_fill_this_week_and_next_in_every_office) @ 9184f9d`), and a rerun adds nothing (`tests/test_demo.py:55-64 (test_rerun_adds_no_rooms_or_bookings) @ 9184f9d`).

**Not covered** (git grep over `tests` at `9184f9d`):

- **Cancelling an ended booking.** Nothing matches `ALREADY_ENDED|already (ended|over|finished)|has ended`, so the check at `roombooker/bookings/service.py:359-360 (booking_to_cancel) @ 9184f9d` is untested.
- **A booking in progress.** No test closes a room during one or cancels one.
- **Reopening a room with bookings.** Reopening is tested only with no bookings present (`tests/test_rooms.py:164-191 (test_close_after_confirmation_then_reopen) @ 9184f9d`), so no test asserts that reopening restores no bookings.
- **Closing an already-closed room**, the trigger's `NOT OLD.is_closed` guard. No test.
- **`upcoming_bookings`.** No test mentions it by name.
- **Boundaries at "now".** All times are at least a day from the real clock.

## Where the answers meet

- **`roombooker/bookings/service.py:353-361 (booking_to_cancel) @ 9184f9d`** is reached from questions 1, 2 and 5. It is the only Python code that refuses an action on an ended booking: it rejects `end_at <= utc_now()` with `InvalidBooking(ALREADY_ENDED)`, and rejects non-organisers with `NotAllowed(ONLY_ORGANISER)`. No test covers the ended branch.
- **`migrations/versions/0003_bookings.py:23-34 (_GUARD) @ 9184f9d`** is reached from questions 2, 3 and 5. It aborts with `room_closed` for a closed room and with `booking_conflict` for any same-room overlap, counting every existing row whatever its time.
- **`migrations/versions/0003_bookings.py:84-95 (upgrade) @ 9184f9d`**, the close trigger, is reached from questions 1, 2, 3 and 5. It deletes only rows with `start_at` after SQLite's now, on an open-to-closed change.
- **`roombooker/bookings/service.py:302-350 (book) @ 9184f9d`** is reached from questions 2 and 3. It maps the guard's aborts to `RoomClosed` and `BookingConflict` and re-raises any other `IntegrityError`.

## Open questions

- **Question 4 stopped at the squash commit `5f72d52`.** The next ask would be: in the `greenfield-done` tag's history, which commits introduced `cancel`, `delete_booking`, the attendee cascade and `rooms_close_cancels_future_bookings`, and what do they and the planning text say about AD-13 and OQ-3? This needs the tag fetched into the clone, or read access to the origin repository; on 2026-11-13 the user chose not to fetch either.

## Prior documents

- `docs/decisions/adr-closing-a-room-deletes-its-future-bookings.md`: researchers reached it from the code (question 3, question 4).
- `docs/decisions/adr-case-insensitive-matching-in-python-not-sqlite.md`: listed, not opened.
- No earlier research documents exist on this subject.

## Decisions found

**Calendar event UIDs carry a content hash beside the booking id.** `d7c6ceb "feat(calendar): private calendar feed per person, with reset on My bookings"` changed the UID from `booking-{id}@roombooker` (introduced in `1f90dba "feat(bookings): add "Add to calendar" .ics download to a booking's details page"`) to `booking-{id}-{hash}@roombooker`, hashing room, start, end and title (`roombooker/bookings/ical.py:52-64 (uid) @ 9184f9d`). The rationale in its docstring and commit message is "so a booking id SQLite reuses after a delete is a new event, never an update of the old." `bookings.id` has no AUTOINCREMENT (`migrations/versions/0003_bookings.py:40 (upgrade) @ 9184f9d`).

- *Hard to reverse:* subscribed calendars key events by UID, so changing the scheme again re-creates every event in every subscriber's calendar.
- *Surprising without context:* any change to a booking's room, times or title yields a new UID, so calendars see it as a delete plus an add rather than an update.
- *A real trade-off:* stable per-booking identity was given up to avoid a reused id updating someone else's old event.

Proposed ADR: `docs/decisions/adr-calendar-uids-hash-booking-content.md`. User's answer (2026-11-13): leave it; no ADR written.
