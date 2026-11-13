**Digest: how a booking stops being active @ 9184f9d**

**Short answer.** A booking has no status or "cancelled" column. It is a row with `start_at`/`end_at` UTC text (roombooker/bookings/store.py:16-25 bookings @ 9184f9d). It stops being active in one of three ways:
1. **End time passes.** Nothing is written. Each read compares `end_at` with the current time.
2. **The organiser cancels.** The row is hard-deleted in Python.
3. **A manager closes the room.** A database trigger hard-deletes the room's bookings that have not started yet.

Deactivating a person does nothing to bookings.

**1. End time passes (computed at read time, no write)**
- **Load-bearing:** `end_at` is the only end marker. The schema has `CheckConstraint("end_at > start_at")` (migrations/versions/0003_bookings.py:54-56 upgrade @ 9184f9d) and no status or cancelled_at column.
- Where "ended" is computed:
  - The upcoming list filters `end_at > after`, with `after` = `clock.utc_now()` (roombooker/bookings/store.py:54-63 upcoming_for_organiser; roombooker/bookings/service.py:200-205 upcoming_bookings @ 9184f9d).
  - The details page sets `has_ended = booking.end_at <= uk.utc_now()` (roombooker/bookings/web.py:257 booking_details @ 9184f9d). The template uses it to hide the Cancel link: `{% if booking.can_cancel and not has_ended %}` (roombooker/templates/bookings/details.html:34 @ 9184f9d).
  - The service rejects cancelling once `view.end_at <= clock.utc_now()` and raises `InvalidBooking(ALREADY_ENDED)`, HTTP 422 (roombooker/bookings/service.py:359-360 booking_to_cancel; :46 ALREADY_ENDED; :49-50 InvalidBooking @ 9184f9d).
  - The feed only includes bookings that end after now minus 30 days (roombooker/bookings/service.py:285-290 feed_calendar @ 9184f9d).
- Ended bookings stay in the table forever. No Python code or trigger purges them. A search for `delete(` and `DELETE FROM` across `*.py` found only the two delete paths below.

**2. Cancellation by the organiser (hard delete in Python)**
- Call stack:
  - `GET /bookings/{id}/cancel` → confirm_cancel (roombooker/bookings/web.py:299-314 @ 9184f9d) → `service.booking_to_cancel`. It renders details.html with `confirming=True`, which shows the POST form (roombooker/templates/bookings/details.html:22-29 @ 9184f9d).
  - `POST /bookings/{id}/cancel` → cancel (roombooker/bookings/web.py:317-322 @ 9184f9d), which redirects 303 to `/rooms?notice=cancelled`.
    - service.cancel (roombooker/bookings/service.py:364-371 @ 9184f9d), **load-bearing**:
      - calls `booking_to_cancel` again (:353-361)
      - then `store.begin_immediate` (roombooker/bookings/store.py:35-42)
      - then `store.delete_booking` (roombooker/bookings/store.py:118-120 delete_booking: `DELETE FROM bookings WHERE id=…`)
      - then commit and a log line.
- Checks that reject on this path:
  - `_get_row` raises `BookingNotFound` (404, "It may have been cancelled") if the id is ≤0, above `2**63-1`, or missing (roombooker/bookings/service.py:267-271 _get_row; :61-63 @ 9184f9d).
  - `NotAllowed(ONLY_ORGANISER)` if the actor is not the organiser (service.py:356-358; can_cancel_booking :93-95 @ 9184f9d).
  - `InvalidBooking(ALREADY_ENDED)` if the booking has ended (service.py:359-360). A booking that has already started but not ended can still be cancelled.
- The ended check (in `booking_to_cancel`) runs before `begin_immediate`, outside the write lock (service.py:366-367 @ 9184f9d).
- Attendee rows go with the booking through `ON DELETE CASCADE` on `booking_attendees.booking_id` (migrations/versions/0003_bookings.py:60-69 @ 9184f9d). This needs `PRAGMA foreign_keys=ON`, which every connection sets (roombooker/core/db.py:12-16 PRAGMAS, :32 make_engine @ 9184f9d).

**3. Closing a room (hard delete by a database trigger)**
- Call stack:
  - `POST /rooms/{id}/close` → close_room (roombooker/rooms/web.py:213-217 @ 9184f9d). A GET confirm page comes first (:202-210).
    - rooms.service.close_room (roombooker/rooms/service.py:215-218 @ 9184f9d) → `_set_closed(..., is_closed=True)` (:205-212). `_require_manager` rejects anyone who is not a manager of the room's office (:208), then it commits.
      - rooms.store.set_closed (roombooker/rooms/store.py:49-50 @ 9184f9d): `UPDATE rooms SET is_closed=…`. The `is_closed` column is defined at migrations/versions/0002_rooms.py:31 @ 9184f9d.
        - **Load-bearing:** trigger `rooms_close_cancels_future_bookings` (migrations/versions/0003_bookings.py:84-95 upgrade @ 9184f9d). It is `AFTER UPDATE OF is_closed ON rooms WHEN NEW.is_closed AND NOT OLD.is_closed` and runs `DELETE FROM bookings WHERE room_id = NEW.id AND start_at > strftime('%Y-%m-%dT%H:%M:%SZ','now')`.
- What follows from the trigger as written:
  - Only bookings that have not started are deleted. A booking in progress, or one whose `start_at` equals the current time, survives in the closed room.
  - Past bookings stay.
  - Reopening the room restores nothing.
  - Attendee rows cascade as in path 2.
- The trigger takes "now" from SQLite's `'now'`, not from `core.time.utc_now()`. Paths 1 and 2 use `utc_now()`, so the two clock sources are separate.
- Python deletes nothing extra here. `close_room` only updates the room (its docstring at rooms/service.py:216-217 says so). The `_set_closed` path does not call `begin_immediate`.
- Related guard (it blocks new bookings rather than ending existing ones): the `_GUARD` in `bookings_no_overlap_insert`/`_update` raises `room_closed` for bookings in a closed room (migrations/versions/0003_bookings.py:23-34, :77-83 @ 9184f9d).

**Not an end path: deactivating a person**
- `load_people` sets `active=False` on anyone missing from the CSV and its docstring says "Never deletes" (roombooker/people/store.py:144-174 load_people @ 9184f9d). seed.py only logs those ids (roombooker/seed.py:134-135 @ 9184f9d).
- No trigger exists on `people`. A search for `TRIGGER` in `migrations/` found only the three in 0003.
- Bookings organised or attended by an inactive person stay as they are. The active flag only stops someone being added as an attendee in future (roombooker/bookings/service.py:322-323 book; :256-258 attendee_choices @ 9184f9d).

**Searched for and not found @ 9184f9d** (with `git grep`, excluding tests, `_bmad*` and `.claude`):
- any status, cancelled or soft-delete column on bookings
- any `UPDATE` of `end_at` to shorten a booking (the update trigger exists, but no Python code updates bookings)
- any purge or expiry job for past bookings
- any delete of bookings in `seed.py` or `demo.py`
- any trigger on `people`

The migration list is 0001–0004, and 0004 only adds `feed_token`.

**Budget:** 12 of 15 files read. Not opened: roombooker/demo.py (the grep showed no delete in it), the two ADRs, and the tests.
