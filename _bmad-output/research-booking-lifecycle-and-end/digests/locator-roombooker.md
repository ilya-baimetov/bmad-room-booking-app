Digest for `roombooker/` Python files at 9184f9d (templates and static left out). All searches used `git grep` / `git show` / `git log` at the commit.

**Background that applies to every question.** The `bookings` table has no status column, no cancelled/deleted timestamp and no soft-delete flag. Its only columns are `id`, `room_id`, `organiser_id`, `title`, `start_at` and `end_at`, and times are stored as UTC text that sorts in time order. A booking ends in one of three ways: its `end_at` passes (nothing is written), the organiser cancels it (a row DELETE), or its room is closed (a DB trigger DELETE, only for bookings that have not started). The trigger SQL is in `migrations/`, which is outside my area. I only see it referenced from here.

### Q1: how a booking stops being active
- `roombooker/bookings/store.py:16 (bookings) @ 9184f9d`: the table definition. No status or deleted columns; `end_at` at :24.
- `roombooker/bookings/store.py:118 (delete_booking) @ 9184f9d`: a hard DELETE by id. Its docstring says attendees go too via "ON DELETE CASCADE, AD-13".
- `roombooker/bookings/service.py:364 (cancel) @ 9184f9d`: "Cancel (delete, AD-13)". It runs `begin_immediate`, then `delete_booking`, then commit, then logs `cancel booking_id=`.
- `roombooker/bookings/service.py:353 (booking_to_cancel) @ 9184f9d`: guards the cancel. Non-organisers get `NotAllowed(ONLY_ORGANISER)`. If `end_at <= utc_now()` it raises `InvalidBooking(ALREADY_ENDED)`.
- `roombooker/bookings/service.py:46 (ALREADY_ENDED) @ 9184f9d`, `:63 (BookingNotFound) @ 9184f9d`: the error messages. BookingNotFound says "It may have been cancelled."
- `roombooker/bookings/service.py:93 (can_cancel_booking) @ 9184f9d`: only the organiser can cancel.
- `roombooker/bookings/web.py:299 (confirm_cancel) @ 9184f9d` and `:317 (cancel) @ 9184f9d`: GET/POST `/bookings/{id}/cancel`, which redirects to `/rooms?notice=cancelled`. Notice text is at `:43 (NOTICES)`.
- `roombooker/rooms/service.py:215 (close_room) @ 9184f9d`: docstring says "A database trigger deletes its bookings that have not started yet in the same statement" and cites `docs/decisions/adr-closing-a-room-deletes-its-future-bookings.md`. It goes through `_set_closed` at `:205`, then `roombooker/rooms/store.py:49 (set_closed) @ 9184f9d`, which is a plain UPDATE of `is_closed`. The Python code never deletes bookings on close; the trigger does.
- `roombooker/rooms/web.py:213 (close_room) @ 9184f9d`, `:202 (confirm_close)`: POST/GET `/…/{room_id}/close`.
- `roombooker/bookings/web.py:257 (booking_details) @ 9184f9d`: `has_ended = booking.end_at <= uk.utc_now()`. Ending by time is only ever computed, never stored.
- `roombooker/people/store.py:144 (load_people) @ 9184f9d`: "mark anyone missing inactive. Never deletes." Deactivating a person does not touch their bookings. I found no code path that does.

### Q2: what reads `end_at` or depends on a booking existing or being removed
- `roombooker/bookings/store.py:45 (overlapping) @ 9184f9d`: `start_at < end_at AND end_at > start_at`, across every room.
- `roombooker/bookings/store.py:54 (upcoming_for_organiser) @ 9184f9d`: `end_at > after`.
- `roombooker/bookings/store.py:66 (for_person) @ 9184f9d`: overlap filter, for bookings the person organises or attends.
- `roombooker/bookings/service.py:123 (free_rooms) @ 9184f9d`: rooms with an overlapping booking count as taken, and closed rooms are left out.
- `roombooker/bookings/service.py:191 (bookings_in_slot)`, `:200 (upcoming_bookings)` (uses `utc_now`, limit 20), `:208 (bookings_for_person)`, `:225 (slot_problem)` (an advisory overlap and closed check), all `@ 9184f9d`.
- `roombooker/bookings/service.py:151 (_views) @ 9184f9d`: turns `end_at` text into datetimes and sets `can_cancel`.
- `roombooker/bookings/service.py:302 (book) @ 9184f9d`: maps trigger aborts `room_closed` / `booking_conflict` (from IntegrityError) to `RoomClosed` / `BookingConflict`.
- `roombooker/bookings/service.py:107 (check_slot) @ 9184f9d`: works out `end_at`. `allow_past` lifts the "from now" rule, for demo data only.
- iCal download: `roombooker/bookings/service.py:279 (booking_calendar) @ 9184f9d` and `roombooker/bookings/web.py:270 (booking_calendar) @ 9184f9d`, at `/bookings/{id}/calendar.ics`.
- iCal feed: `roombooker/bookings/service.py:285 (feed_calendar) @ 9184f9d` covers bookings that overlap the window from 30 days back to `FEED_END`. Also `roombooker/calendar/service.py:25 (feed) @ 9184f9d` and `roombooker/calendar/web.py:156 (feed) @ 9184f9d`.
- `roombooker/bookings/ical.py:52 (uid) @ 9184f9d`: the UID hash covers room, start, end and title, "so a booking id SQLite reuses after a delete is a new event". This code exists only because of the delete model.
- `roombooker/bookings/ical.py:67 (_event) @ 9184f9d`: writes `DTEND` from `end_at` and always `STATUS:CONFIRMED`. Cancelled events are never written; they just drop out of the feed.
- Calendar view: `roombooker/calendar/service.py:18 (my_bookings) @ 9184f9d` and `roombooker/calendar/web.py:68 (my_bookings) @ 9184f9d`, which buckets bookings by day using `end_at > bounds[i]` (:91).
- Rooms page: `roombooker/bookings/web.py:86 (rooms) @ 9184f9d` shows upcoming and in-slot bookings. `:281 (_book_again_query)` takes the length from `end_at - start_at`. `:76 (_slot_text)`.
- Demo and seed: `roombooker/demo.py:176 (load_demo) @ 9184f9d` books with `allow_past=True`, skips slots that are taken or rooms that are closed, and catches `BookingConflict` / `RoomClosed`. Its module docstring is at `:1`. It is called from `roombooker/seed.py:141 (_load_demo) @ 9184f9d`, behind the `--demo-bookings` flag.

### Q3: how the overlap and close triggers decide which bookings count
The trigger SQL is not in my area. From here:
- `roombooker/bookings/service.py:1 (module docstring) @ 9184f9d` and `:312 (book)` say "The database triggers refuse overlaps and closed rooms (AD-4)". Their abort reasons contain `booking_conflict` and `room_closed` (:344-347).
- `roombooker/bookings/store.py:3 (module docstring) @ 9184f9d` says the triggers are created by Alembic (AD-10).
- `roombooker/rooms/service.py:216 (close_room) @ 9184f9d`: the close trigger deletes bookings "that have not started yet". By this wording, a booking already in progress survives.
- The Python overlap logic (`store.py:45`, `:66`) uses half-open `[start, end)` and has no past/future filter. Removed bookings are rows that no longer exist, so there is no current-vs-removed check to make.

### Q4: why the end is a delete
- `roombooker/bookings/service.py:365 (cancel) @ 9184f9d` and `roombooker/bookings/store.py:119 (delete_booking) @ 9184f9d` both cite AD-13, a decision ID whose text is not in this area.
- `roombooker/rooms/service.py:217 (close_room) @ 9184f9d` cites `docs/decisions/adr-closing-a-room-deletes-its-future-bookings.md`, which is outside my area.
- `roombooker/bookings/ical.py:53 (uid) @ 9184f9d` names one consequence: SQLite reuses booking ids after a delete.
- For contrast, people are deactivated rather than deleted: `roombooker/people/store.py:145 (load_people) @ 9184f9d`.
- History can't answer this. The commit has 11 commits in total. Every `roombooker/` file traces back to `5f72d52 chore: remove BMad files and the walkthrough log`, which appears to be a squashed import. `git log -S delete_booking` and `git log -S adr-closing` both return only 5f72d52. Later commits that touch the booking files (`36d0004`, `1f90dba`, `d7c6ceb`) add Book again, the .ics download and the feed. None of them change how a booking ends.

### Q5: tests
Tests are outside `roombooker/`. My area has no test code.

### Searched, nothing found (9184f9d, `roombooker/` excluding templates and static)
- `status|cancelled_at|deleted_at|is_cancelled|soft` as booking columns: none. The only `STATUS` is the fixed `STATUS:CONFIRMED` at ical.py:79.
- `ends_at|end_time|ended`: none, apart from the ALREADY_ENDED message and the `has_ended` local. The column is named `end_at`.
- Python code that deletes bookings on room close or person deactivation: none. Close is only an UPDATE of `is_closed`.
- Archiving or purging of past bookings: none.
