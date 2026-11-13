Digest for question 5, from code read through git at the commit; nothing run. Full 15-file budget used.

## How the tests control time and "now"
- **Load-bearing:** nothing in the tests freezes or fakes the clock. No test uses freezegun or patches `utc_now`. Policy stated: "Times are relative to the real clock: the close-room trigger uses SQLite's own "now"." `tests/test_bookings.py:3` (module docstring) @ 9184f9d. The only `monkeypatch` uses set env vars and one rooms-service helper (`tests/conftest.py:28-29` db_path; `tests/test_people_web.py:90`; `tests/test_rooms.py:240`) @ 9184f9d.
- **Load-bearing:** two separate clocks. Python: `datetime.now(UTC)` at `roombooker/core/time.py:15-17` (utc_now) @ 9184f9d. Trigger: `start_at > strftime('%Y-%m-%dT%H:%M:%SZ', 'now')` at `migrations/versions/0003_bookings.py:86-92` (upgrade, rooms_close_cancels_future_bookings) @ 9184f9d. Faking the Python clock would not move SQLite's.
- Future dates from the real UK date: `uk_day(n)` at `tests/test_bookings.py:32-33` (uk_day); `book` fixture defaults to `uk_day(1)` 10:00 for 60 min at `tests/test_bookings.py:68-86` (book) @ 9184f9d. Same pattern in `tests/test_calendar.py:30,42,66,81`, `tests/test_demo.py:46`, `tests/e2e/test_book_a_room.py:20,58`, `tests/e2e/test_my_bookings.py:20` @ 9184f9d.
- Past/far-future bookings written straight into SQLite: `insert_booking` "for times the web refuses (past, far ahead)" at `tests/test_bookings.py:323-335` (insert_booking); inline raw inserts at `tests/test_bookings.py:279-284` and `:244-253` @ 9184f9d. Fixed past dates (2020-01-07, 2020-01-01, 2026-07-07) as ended bookings; fixed 2027/2030 dates for DST and trigger cases.
- `test_feed` builds its 30-day window from `uk.utc_now()` minus 31 or 29 days: `tests/test_feed.py:75-83` @ 9184f9d.
- Only fixed clock: `STAMP = datetime(2026, 11, 13, 8, 30, tzinfo=UTC)` passed to `ical.calendar`: `tests/test_ical.py:10,36` @ 9184f9d.
- Harness: temp SQLite migrated through Alembic `tests/conftest.py:19-33` (migrate_to_head, db_path); `TestClient(create_app(), follow_redirects=False)` `tests/conftest.py:65-68` (client); `person_id` cookie `tests/test_bookings.py:42-47` (act); e2e one Alembic + seed + uvicorn subprocess per session `tests/e2e/conftest.py:59-90` (live_server); README `README.md:112-117` (Tests) @ 9184f9d.

## Lifecycle stages and the tests that cover them
- **Create.** Happy path with attendees `tests/test_bookings.py:143-166` (test_book_with_attendees_and_details_for_everyone). Refusals keep the typed form — overlap 409, IN_THE_PAST 422, TOO_FAR_AHEAD 422, NOT_ON_QUARTER 422, BAD_LENGTH (255 or 0) 422, NEEDS_TITLE 422, closed room 409 — `tests/test_bookings.py:184-212` (test_refused_bookings_keep_the_form) @ 9184f9d.
  - Concurrent same-slot booking, Barrier threads, exactly one `BookingConflict`: `tests/test_bookings.py:215-238` (test_two_people_booking_the_same_slot_at_once) @ 9184f9d.
  - **Load-bearing:** DB backstop — raw INSERT and UPDATE refused with `booking_conflict`, insert into closed room with `room_closed`: `tests/test_bookings.py:241-253` (test_database_refuses_overlaps_and_closed_rooms) @ 9184f9d.
- **Removal by organiser cancel.** **Load-bearing:** `tests/test_bookings.py:256-273` (test_only_the_organiser_cancels) @ 9184f9d: non-organiser (even the office manager) 403 on GET and POST with `ONLY_ORGANISER`; organiser gets confirmation then POST → 303 `/rooms?notice=cancelled`; `bookings` and `booking_attendees` rows gone, details 404; slot bookable again.
  - Leaves the feed `tests/test_feed.py:113-119` (test_cancelled_booking_leaves_the_feed); `.ics` 404 `tests/test_bookings.py:566-572` (test_add_to_calendar_unknown_or_cancelled_booking_is_404); reused id gets a different UID, asserting `again == first` `tests/test_feed.py:240-250` (test_reused_booking_id_gets_a_different_uid); e2e cancel `tests/e2e/test_book_a_room.py:15-52` (test_find_book_and_cancel) @ 9184f9d.
- **Removal by closing the room.** **Load-bearing:** `tests/test_bookings.py:276-291` (test_closing_a_room_cancels_its_future_bookings) @ 9184f9d: one future booking plus a raw-inserted 2020 booking; manager closes; only 2020 row survives, attendees deleted, future booking 404. Exercises the trigger against SQLite's real now.
  - Feed side effect `tests/test_feed.py:122-131` (test_closing_a_room_removes_its_bookings_from_the_feed); confirmation text "its future bookings are cancelled", no bookings present, `tests/test_rooms.py:164-190` (test_close_after_confirmation_then_reopen); e2e close/reopen with no bookings `tests/e2e/test_manage_rooms.py:69` @ 9184f9d.
- **Ended bookings, read-only.** "Book again" shown `tests/test_bookings.py:338-349` (test_book_again_link_only_for_the_organiser); "Add to calendar" shown `tests/test_bookings.py:526-534` (test_add_to_calendar_writes_a_bst_booking_in_utc); Book again with no-longer-valid time `tests/test_bookings.py:432-452` (test_book_again_time_no_longer_valid); Book again on room closed later `tests/test_bookings.py:455-466` (test_book_again_room_closed); feed keeps ended-29-days, drops ended-31-days (`FEED_DAYS_BACK = 30`) `tests/test_feed.py:68-92`; `roombooker/bookings/service.py:33,288-290` @ 9184f9d.
- **Seed/demo.** Fill this week and next Mon–Fri, rerun adds none: `tests/test_demo.py:39-64` @ 9184f9d.

## Checks on the removal path that reject a request
- `roombooker/bookings/service.py:356-358` (booking_to_cancel) @ 9184f9d: `NotAllowed(ONLY_ORGANISER)`. Tested.
- `roombooker/bookings/service.py:359-360` (booking_to_cancel) @ 9184f9d: `InvalidBooking(ALREADY_ENDED)` once `end_at <= utc_now()`. **Load-bearing:** no test covers this.
- `migrations/versions/0003_bookings.py:88-92` @ 9184f9d: deletes only `start_at > now`, only on false→true. Past-kept side tested; boundaries not.

## Searched for and not found (git grep over `tests` @ 9184f9d)
- Cancelling an ended booking: no match for `ALREADY_ENDED|already (ended|over|finished)|has ended`; no test cancels a past-inserted booking.
- A booking in progress: no test closes a room during one; none cancels one; grep `in progress` none.
- Reopening does not restore bookings: not asserted (grep `reopen.*book` none).
- Closing an already-closed room (`NOT OLD.is_closed`): no test.
- `upcoming_bookings` (`roombooker/bookings/service.py:200-205`): grep `upcoming` none in tests.
- Clock control: no freezegun, `time_machine`, or monkeypatch of `utc_now`/`uk_now`.
- Boundaries at now: none; all times a day or more from the real clock.
- Wall-clock dependence: `uk_day(85)` "+7 > 90", `uk_day(89)`, e2e "next week" at `tests/e2e/test_my_bookings.py:46`.

Budget: 15 files. Not read: rest of `tests/test_rooms.py`, parts of e2e files, `bookings/store.py`, `bookings/web.py` (ALREADY_ENDED HTTP mapping), `pyproject.toml:27`.
