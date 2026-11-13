Commit 9184f9d. All reads went through `git show` / `git grep` at that commit. I opened 14 of the 15 budgeted files: the 13 assigned (4 of them templates) plus a slice of `roombooker/rooms/service.py`. `roombooker/core/db.py` and `roombooker/people/service.py` were seen only as grep hits.

## Storage and schema
- `migrations/versions/0003_bookings.py:54-56 (upgrade) @ 9184f9d`: `start_at` and `end_at` are NOT NULL strings, with CHECK `end_at > start_at` (`ck_bookings_end_after_start`). This rejects any row whose end is not after its start.
- `migrations/versions/0003_bookings.py:58-59 (upgrade) @ 9184f9d`: the only indexes are `(room_id, start_at)` and `(organiser_id)`. There is no index containing `end_at`.
- `migrations/versions/0003_bookings.py:65-66 (upgrade) @ 9184f9d`: `booking_attendees.booking_id` uses ON DELETE CASCADE, so removing a booking also removes its attendees. This depends on `PRAGMA foreign_keys=ON` at `roombooker/core/db.py:15 @ 9184f9d` (grep hit only).
- `roombooker/bookings/store.py:16-25 (bookings) @ 9184f9d`: the Table describes `end_at` as String.

## Overlap guard (load-bearing)
- `migrations/versions/0003_bookings.py:23-34 (_GUARD) @ 9184f9d`, **load-bearing**. It aborts with `room_closed` if the room's `is_closed` is set. It aborts with `booking_conflict` if another booking in the same room satisfies `other.start_at < NEW.end_at AND NEW.start_at < other.end_at`. That is a half-open interval test, and it excludes the row itself via `other.id IS NOT NEW.id`.
- `migrations/versions/0003_bookings.py:77-83 @ 9184f9d`: `_GUARD` runs BEFORE INSERT, and BEFORE UPDATE OF `room_id, start_at, end_at`. No Python code issues an UPDATE on bookings: the store has only `insert` and `delete_booking`.

## Removal paths (load-bearing)
- `migrations/versions/0003_bookings.py:84-95 (rooms_close_cancels_future_bookings) @ 9184f9d`, **load-bearing**. AFTER UPDATE OF `is_closed` on rooms, when a room goes from open to closed, it runs `DELETE FROM bookings WHERE room_id = NEW.id AND start_at > strftime('%Y-%m-%dT%H:%M:%SZ','now')`.
  - The filter is on `start_at`, not `end_at`. A booking that is in progress, or already finished, survives the close.
  - "now" includes real seconds, while stored times always end in `:00Z`.
- `roombooker/rooms/service.py:205-219 (_set_closed, close_room) @ 9184f9d`: `close_room` → `store.set_closed` → commit. It does no booking deletion in Python; the docstring points to the trigger.
- `roombooker/bookings/store.py:118-120 (delete_booking) @ 9184f9d`: this is the only Python DELETE on bookings, by id. A grep for `DELETE FROM|delete(` across `*.py`, excluding tests, found only this and the trigger.
- `roombooker/bookings/service.py:353-361 (booking_to_cancel) @ 9184f9d`, **load-bearing**. It raises `NotAllowed(ONLY_ORGANISER)` if the viewer is not the organiser, and `InvalidBooking(ALREADY_ENDED)` if `view.end_at <= clock.utc_now()`.
- `roombooker/bookings/service.py:364-371 (cancel) @ 9184f9d`: calls `booking_to_cancel` (the end-time check) first, then `begin_immediate`, then `delete_booking`, then commit. The end-time check runs before the write lock is taken.
- `roombooker/bookings/web.py:299-314 (confirm_cancel) @ 9184f9d`: GET calls `booking_to_cancel`, so the end check applies, and renders `details.html` with `has_ended=False`.
- `roombooker/bookings/web.py:317-322 (cancel) @ 9184f9d`: POST calls `service.cancel`, then redirects to `/rooms?notice=cancelled`.

## Queries that filter on end_at
- `roombooker/bookings/store.py:45-51 (overlapping) @ 9184f9d`: any room where `start_at < end_at_param AND end_at > start_at_param`, ordered by `start_at, id`.
- `roombooker/bookings/store.py:54-63 (upcoming_for_organiser) @ 9184f9d`: `organiser_id == id AND end_at > after`, with LIMIT.
- `roombooker/bookings/store.py:66-80 (for_person) @ 9184f9d`: the same overlap test as `overlapping`, restricted to bookings the person organises or attends (subquery on `booking_attendees`).
- `roombooker/bookings/store.py:83-84 (get) @ 9184f9d`: fetch by id. Through `service._get_row` (`service.py:267-271`) it becomes `BookingNotFound` (404) when the row is missing or the id is outside 1..2^63-1.

## Service call sites
- `roombooker/bookings/service.py:107-120 (check_slot) @ 9184f9d`, **load-bearing**. It computes the end as `start + length`. It rejects:
  - a start that is not on a quarter hour (`NOT_ON_QUARTER`)
  - a length outside 15–240 minutes or not a multiple of 15 (`BAD_LENGTH`)
  - a start before now, unless `allow_past` (`IN_THE_PAST`)
  - a start more than 90 days ahead (`TOO_FAR_AHEAD`)

  It does not check the end against now.
- `service.py:123-148 (free_rooms) @ 9184f9d`: takes the end from `check_slot`, runs `store.overlapping` to build the set of taken room ids, and also drops closed rooms in Python (line 136).
- `service.py:151-188 (_views) @ 9184f9d`: `end_at = clock.from_text(row.end_at)` (line 170) and puts it in `BookingView.end_at`. Every view-producing path goes through here. It looks up `rooms[row.room_id]` from `all_rooms`, which includes closed rooms.
- `service.py:191-197 (bookings_in_slot) @ 9184f9d`: end is `start + length` computed directly, without `check_slot`, then `store.overlapping` → `_views`.
- `service.py:200-205 (upcoming_bookings) @ 9184f9d`: `store.upcoming_for_organiser(after=utc_now(), limit=20)`. A booking stays listed until its end passes.
- `service.py:208-214 (bookings_for_person) @ 9184f9d`: `store.for_person` → `_views`.
- `service.py:225-240 (slot_problem) @ 9184f9d`: returns the closed message if the room is closed (checked before `check_slot`). Otherwise it calls `check_slot` and returns the taken message if `store.overlapping` has a row in this room. It describes itself as advisory only.
- `service.py:279-282 (booking_calendar) @ 9184f9d`: `get_booking` → `ical.calendar([view])`. There is no ended or closed filter.
- `service.py:285-290 (feed_calendar) @ 9184f9d`: `bookings_for_person(now - 30 days, FEED_END)`, where `FEED_END = 9999-12-31T23:59Z` (line 35). The feed therefore holds bookings whose end is after 30 days ago.
- `service.py:302-350 (book) @ 9184f9d`, **load-bearing**. It computes the end with `check_slot` (line 316), then `begin_immediate` → `store.insert(... to_text(end_at) ...)`. It maps an IntegrityError containing `room_closed` to `RoomClosed` (409) and one containing `booking_conflict` to `BookingConflict` (409); any other IntegrityError is re-raised. It raises `InvalidBooking(ATTENDEE_GONE)` for an inactive attendee.
- `roombooker/calendar/service.py:18-22 (my_bookings) @ 9184f9d`: passes straight through to `bookings_for_person`.
- `roombooker/calendar/service.py:25-31 (feed) @ 9184f9d`: token → person, or None → `feed_calendar`.

## iCal
- `roombooker/bookings/ical.py:52-64 (uid) @ 9184f9d`: the UID hash covers the room id, `start_at`, `end_at` and title. Changing the end time produces a different UID, so calendar apps treat it as a new event rather than an update.
- `ical.py:67-79 (_event) @ 9184f9d`: writes `DTEND:{clock.ical_utc(booking.end_at)}` (line 73) and always `STATUS:CONFIRMED`.

## Web call sites
- `roombooker/bookings/web.py:76-78 (_slot_text) @ 9184f9d`: end is `start + length`, shown as a UK clock time. Used at lines 121 and 152.
- `bookings/web.py:85-126 (rooms) @ 9184f9d`: `upcoming_bookings` (line 111), `free_rooms` (119) and `bookings_in_slot` (120). Because `free_rooms` runs first, `check_slot` validates the slot before `bookings_in_slot` on this page.
- `bookings/web.py:129-178 (_form_page) @ 9184f9d`: calls `slot_problem` (line 154).
- `bookings/web.py:246-267 (booking_details) @ 9184f9d`: the booked notice shows `end_at` (255), and `has_ended = booking.end_at <= uk.utc_now()` (257) decides whether the Cancel button appears.
- `bookings/web.py:270-278 (booking_calendar) @ 9184f9d`: serves the one-event `.ics` download.
- `bookings/web.py:281-296 (_book_again_query) @ 9184f9d`: the length is `(end_at - start_at)` in minutes.
- `roombooker/calendar/web.py:67-121 (my_bookings) @ 9184f9d`: fetches over `[uk_midnight(first), uk_midnight(last+1))` (lines 84-85). It then puts each booking into a day in Python with `b.start_at < bounds[i+1] and b.end_at > bounds[i]` (line 91), so a booking spanning midnight appears on both days. `is_empty` (109) checks whether any booking exists.
- `roombooker/calendar/web.py:156-169 (feed) @ 9184f9d`: returns 404 for a malformed or unknown token, otherwise the feed text with `Cache-Control: private, no-cache`.

## Templates (display of end_at and existence)
- `roombooker/templates/bookings/_item.html:4 @ 9184f9d`: `{{ b.end_at|clock }}`.
- `roombooker/templates/bookings/rooms.html:58-63 @ 9184f9d`: the "Booked then" list from `in_slot`.
- `roombooker/templates/bookings/rooms.html:67-74 @ 9184f9d`: "Your upcoming bookings", with "no upcoming bookings" when the list is empty.
- `roombooker/templates/bookings/details.html:10 @ 9184f9d`: shows `end_at`.
- `roombooker/templates/bookings/details.html:32-34 @ 9184f9d`: Add to calendar link, Book again link, and Cancel shown only when `can_cancel and not has_ended`.
- `roombooker/templates/calendar/my_bookings.html:35 @ 9184f9d`: shows `end_at`. Lines 20-21 and 30-44 render the empty or "Nothing booked" states based on whether bookings exist.

## Seed and demo
- `roombooker/demo.py:176-210 (load_demo) @ 9184f9d`: for each demo booking, it checks whether the slot is already taken in this room via `bookings_service.bookings_in_slot` (end is start + minutes, no `check_slot`), and skips it if taken or `room.is_closed`. Otherwise it calls `bookings_service.book(..., allow_past=True)` and counts a `BookingConflict` or `RoomClosed` as skipped. Room creation goes through `rooms_service.add_room` (line 168).
- `roombooker/seed.py:141-157 (_load_demo) @ 9184f9d`: calls `demo.load_demo` (line 144) and logs bookings added and skipped.

## Two patterns doing the same thing (unranked)
- **Overlap test, written twice.**
  - In SQL: `_GUARD` (`0003_bookings.py:31-32`), per room, enforced.
  - In SQLAlchemy: `store.overlapping` and `store.for_person` (`store.py:49, 75-76`), any room, read-only. `free_rooms`, `slot_problem` and `demo.load_demo` filter the result by room in Python.
- **"Has it ended" check, written twice.** `booking_to_cancel` (`service.py:359`) and `booking_details` (`bookings/web.py:257`) both compare `end_at <= utc_now()`.
- **Closed-room check, in four places.** The trigger guard (`0003_bookings.py:24-25`), plus Python pre-checks in `free_rooms:136`, `slot_problem:234` and `demo.load_demo:192`.

## Searched for and not found at 9184f9d
- Any UPDATE of bookings in Python: only `insert` and `delete` exist in `bookings/store.py`.
- Any Python deletion of bookings when a room closes: grep for `DELETE FROM|delete(` in `*.py`, excluding tests.
- Any index on `end_at`: `0003_bookings.py:58-59` is the only index creation in that migration.
- Any reader of booking end times outside `bookings` and `calendar`: grep for `end_at` across `roombooker`, `migrations` and templates outside the assigned paths found only the three template lines already listed.
- `people/service.py:75 @ 9184f9d` (grep hit only) says inactive people keep their bookings. Deactivating a person does not remove bookings.

Files I did not open: `roombooker/core/time.py` (`to_text`, `from_text`, `ical_utc`, `utc_now`), `roombooker/rooms/store.py` beyond grep, and tests.
