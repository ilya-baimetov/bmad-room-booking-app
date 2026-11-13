I checked `migrations/`, `alembic.ini` and `tests/` (including `tests/e2e`) at commit 9184f9d, using git only and skipping the excluded paths. In this area a booking has no recorded "ended" or "cancelled" state. It is either a row in `bookings` or it is gone. It stops being active by passing its `end_at` (nothing in these files acts on that), by an organiser's cancel (the tests show this deletes the row), or by the closing-a-room trigger deleting it.

**Q1. How a booking stops being active**
- `migrations/versions/0003_bookings.py:54 (upgrade) @ 9184f9d`: `start_at` and `end_at` are plain strings in UTC (`'YYYY-MM-DDTHH:MM:00Z'`, noted as AD-5). `:56` adds the check `ck_bookings_end_after_start`. There is no status, `cancelled_at` or `deleted_at` column. A search for `status|cancelled_at|deleted_at|ended|archiv|soft` across migrations, `alembic.ini` and `tests/conftest.py` at 9184f9d found nothing.
- `migrations/versions/0003_bookings.py:86 (upgrade) @ 9184f9d`: the trigger `rooms_close_cancels_future_bookings` runs `AFTER UPDATE OF is_closed ON rooms`. It does a real `DELETE FROM bookings` (lines 90–92). It is the only database trigger that ends bookings.
- `migrations/versions/0003_bookings.py:66 (upgrade) @ 9184f9d`: `booking_attendees.booking_id` has `ondelete="CASCADE"`, so deleting a booking also deletes its attendee rows.
- `migrations/versions/0002_rooms.py:31 (upgrade) @ 9184f9d`: the `rooms.is_closed` flag, which the trigger watches.
- `tests/test_bookings.py:256 (test_only_the_organiser_cancels) @ 9184f9d`: cancelling is `POST /bookings/{id}/cancel`. Afterwards the `bookings` and `booking_attendees` tables are both empty (line 271).
- `tests/test_feed.py:247 (test_reused_booking_id_gets_a_different_uid) @ 9184f9d`: after a cancel, SQLite hands the same id to the next booking. This also confirms cancel is a hard delete.
- The cancel and close code paths themselves are in the app code, outside my area.

**Q2. What reads `end_at` or depends on a booking existing**
- `migrations/versions/0003_bookings.py:23 (_GUARD) @ 9184f9d`: the overlap check reads both `start_at` and `end_at`.
- `migrations/versions/0003_bookings.py:58 (upgrade) @ 9184f9d`: indexes `ix_bookings_room_id_start_at` and `ix_bookings_organiser_id`.
- `tests/test_calendar.py:21 (test_shows_bookings_you_organise_and_attend_only) @ 9184f9d`: the My bookings day view shows the time range "09:00–10:00" (line 34). `:40 test_week_runs_monday_to_sunday_by_uk_day` covers a booking near midnight on Sunday.
- `tests/test_bookings.py:526 (test_add_to_calendar_writes_a_bst_booking_in_utc) @ 9184f9d`: the iCal download. `:566 test_add_to_calendar_unknown_or_cancelled_booking_is_404` checks a cancelled booking's `.ics` gives a 404.
- `tests/test_ical.py:19 (view) @ 9184f9d`: `BookingView.end_at` is used to build the event.
- `tests/test_feed.py:113 (test_cancelled_booking_leaves_the_feed) @ 9184f9d`, plus `:122 test_closing_a_room_removes_its_bookings_from_the_feed`, `:240 test_reused_booking_id_gets_a_different_uid` and `:175 test_inactive_persons_feed_is_404`.
- `tests/test_bookings.py:103 (test_free_rooms_own_office_first_with_capacity_filter) @ 9184f9d`: a room that is already booked or closed is left out of the free-rooms list.
- `tests/test_bookings.py:441 (test_book_again_time_no_longer_valid) @ 9184f9d` and `:455 test_book_again_room_closed`: "Book again" for an old booking, which is written straight into the database with a past `end_at`.
- `tests/test_demo.py:14 (_bookings) @ 9184f9d`: demo bookings are read by `start_at` only. `:39` checks they fill this week and next. `:55` checks that re-running the seed adds nothing.
- `tests/test_seed.py:45 (test_reload_updates_by_email_and_never_deletes) @ 9184f9d`: reloading people never deletes anyone.
- e2e: `tests/e2e/test_my_bookings.py:16 (test_week_view_lists_your_booking_and_opens_it) @ 9184f9d` and `tests/e2e/test_book_a_room.py:55 (test_book_again_when_next_week_is_taken) @ 9184f9d`.

**Q3. Which bookings the triggers count**
- `migrations/versions/0003_bookings.py:23 (_GUARD) @ 9184f9d`: the check runs on insert (`bookings_no_overlap_insert`, line 78) and on any update to `room_id`, `start_at` or `end_at` (`bookings_no_overlap_update`, line 81). It counts every row in the same room, past ones included, with no time filter. On update it skips the row itself (`other.id IS NOT NEW.id`). Overlap is half-open (`other.start_at < NEW.end_at AND NEW.start_at < other.end_at`), compared as strings. It first fails with `room_closed` if the room is closed. Deleted bookings simply aren't there to count.
- `migrations/versions/0003_bookings.py:88 (upgrade) @ 9184f9d`: the closing trigger fires only when a room goes from open to closed (`WHEN NEW.is_closed AND NOT OLD.is_closed`). It deletes only rows with `start_at > strftime('%Y-%m-%dT%H:%M:%SZ','now')`, comparing strings against SQLite's own clock. Bookings already in progress or finished are kept. It never looks at `end_at`.

**Q4. Why a delete rather than a recorded state**
- `migrations/versions/0003_bookings.py:5 (module docstring) @ 9184f9d` points to `docs/decisions/adr-closing-a-room-deletes-its-future-bookings.md`. That file exists at 9184f9d, but it is outside my area and I did not read it.
- No reasoning survives in git history. All 3 migrations' history begins at `5f72d52` ("chore: remove BMad files and the walkthrough log", 2026-11-12), and the repo has 11 commits in total.
- I found no written reason why cancel is a hard delete.

**Q5. How lifecycle, end and removal are tested**
- `tests/test_bookings.py:3 (module docstring) @ 9184f9d`: tests run against the real clock, because the close trigger uses SQLite's "now". There is no clock freezing.
- `tests/test_bookings.py:324 (insert_booking) @ 9184f9d`: past bookings are written directly to SQLite, because the web form refuses them.
- `tests/test_bookings.py:241 (test_database_refuses_overlaps_and_closed_rooms) @ 9184f9d`: the triggers are tested at the database level, including touching back-to-back bookings, overlap on insert and on update, and a closed room.
- `tests/test_bookings.py:215 (test_two_people_booking_the_same_slot_at_once) @ 9184f9d`: two people booking the same slot at once; one gets it, one gets `BookingConflict`.
- `tests/test_bookings.py:276 (test_closing_a_room_cancels_its_future_bookings) @ 9184f9d`: a 2020 booking survives the room closing, the future booking and its attendees are deleted, and the future booking then returns 404.
- `tests/test_bookings.py:256 (test_only_the_organiser_cancels) @ 9184f9d`: only the organiser can cancel, the rows are deleted, and the slot can be booked again.
- `tests/test_rooms.py:164 (test_close_after_confirmation_then_reopen) @ 9184f9d`: the closing confirmation says "its future bookings are cancelled".
- `tests/conftest.py:19 (migrate_to_head) @ 9184f9d`: each test gets a temporary database built through Alembic. `tests/e2e/conftest.py:60 (live_server) @ 9184f9d` runs `alembic upgrade head`.
- `tests/test_feed.py:282 (test_migration_downgrade_and_upgrade_round_trip) @ 9184f9d` round-trips only 0004 to 0003. Nothing tests downgrading 0003 (the triggers).
- e2e: `tests/e2e/test_book_a_room.py:15 (test_find_book_and_cancel) @ 9184f9d` covers booking and cancelling through the UI. `tests/e2e/test_manage_rooms.py:69 (test_add_edit_close_reopen_without_reload) @ 9184f9d` closes a room through the UI but does not check bookings.

**Searched, nothing found (at 9184f9d)**
- No test checks a booking that is under way (started, not yet ended) when its room closes.
- No test shows past bookings blocking new ones.
- No test checks a booking moving from current to past as `end_at` passes.
- No migration or test refers to `end_at` relative to "now".
