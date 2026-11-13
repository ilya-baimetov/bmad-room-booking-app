The two kinds of trigger use different rules. The overlap guard counts **every booking row in the room**, past, current and future, and checks nothing about time. The close trigger deletes only rows whose `start_at` is strictly later than SQLite's own clock. "Removed" has no column: cancelled bookings are deleted rows, so they simply stop counting.

Citations are `path:line (symbol) @ 9184f9d`. **[LB]** marks the load-bearing claims.

**1. Overlap guard (`bookings_no_overlap_insert` / `bookings_no_overlap_update`)**
- **[LB]** Both triggers run the same `_GUARD` body: `migrations/versions/0003_bookings.py:77-79` (upgrade, BEFORE INSERT) and `:80-83` (upgrade, `BEFORE UPDATE OF room_id, start_at, end_at`).
- **[LB]** Check 1 aborts with `room_closed` when `rooms.is_closed` is true for `NEW.room_id`: `0003_bookings.py:24-25 (_GUARD)`. It runs before the overlap check, so a booking in a closed room reports `room_closed` even if it also overlaps.
  - `is_closed` is a non-null Boolean defaulting to false: `migrations/versions/0002_rooms.py:31 (upgrade)`.
  - If the room id doesn't exist, the subquery returns NULL and the guard does not abort. The `fk_bookings_room_id_rooms` foreign key (`0003_bookings.py:44`) catches that instead, with `PRAGMA foreign_keys=ON` from `roombooker/core/db.py:15 (PRAGMAS)`.
- **[LB]** Check 2 aborts with `booking_conflict` when any other booking in the same room overlaps. The rule is `other.start_at < NEW.end_at AND NEW.start_at < other.end_at`, which treats intervals as half-open, so back-to-back bookings are allowed: `0003_bookings.py:26-33 (_GUARD)`.
  - `other.id IS NOT NEW.id` stops an UPDATE from colliding with its own row. On INSERT, `NEW.id` is usually NULL, so every row counts: `:30`.
  - **[LB]** There is no condition on time or status. A finished booking still blocks an overlapping new one. The only way a booking stops counting is deletion.
- The comparison is plain text. That works because times are stored as UTC `YYYY-MM-DDTHH:MM:00Z`, so text order is time order (`roombooker/bookings/store.py:4-5`, module docstring), plus `ck_bookings_end_after_start` (`0003_bookings.py:56`).
- At this commit no app code updates `bookings`. A git grep for `UPDATE|update(` in `roombooker/bookings` found nothing. Writes are only `store.insert` (`store.py:94-115`) and `delete_booking` (`store.py:118-120`), so the UPDATE trigger never fires from the app.

**2. How a trigger abort reaches the user (`book`)**
- `roombooker/bookings/service.py:302-350 (book)`: `begin_immediate` (`:326`, defined at `store.py:35-42`), then the insert. An `IntegrityError` is rolled back and mapped by substring: `room_closed` becomes `RoomClosed` (`:344-345`), `booking_conflict` becomes `BookingConflict` (`:346-347`), and anything else is re-raised (`:348`).
- Before the trigger, `check_slot(start_at, length_minutes, allow_past)` at `:316` rejects some slots; past slots are refused unless `allow_past` is set (only the seed sets it, per the docstring at `:313-314`). I did not open `check_slot`. Because of it, past bookings come from the seed but are still counted by the guard.

**3. The advisory duplicate in Python (`slot_problem`)**
- `roombooker/bookings/service.py:225-240 (slot_problem)` runs the same two checks before the database does:
  - `room.is_closed` returns the closed message (`:234-235`).
  - `store.overlapping` fetches overlapping rows in **any** room using the same half-open test (`store.py:45-51`, `overlapping`, `start_at < end_at AND end_at > start_at`), then Python filters to the room (`:238`).
- It has no time or status filter either. The docstring says it is advisory and that the triggers remain the guarantee (`:231-232`).

**4. Close cascade (`rooms_close_cancels_future_bookings`)**
- **[LB]** `0003_bookings.py:86-93 (upgrade)`: `AFTER UPDATE OF is_closed ON rooms` with `WHEN NEW.is_closed AND NOT OLD.is_closed`. It fires only when a room goes from open to closed. Reopening, or closing an already-closed room, deletes nothing.
- **[LB]** What it deletes: `DELETE FROM bookings WHERE room_id = NEW.id AND start_at > strftime('%Y-%m-%dT%H:%M:%SZ', 'now')` (`:90-92`).
  - "Future" means `start_at` is strictly after the database clock.
  - A booking in progress (`start_at <= now < end_at`) is kept, and so are past bookings.
  - A booking starting at exactly the current second is kept, because the test is `>` not `>=`.
  - `strftime` includes real seconds, while stored values always end in `:00Z`. Both strings are the same length, so the text comparison still works.
- It uses SQLite's `'now'`, not `core.time.utc_now()`. The ADR names this as a trade-off: a fake clock in tests can't move it (`docs/decisions/adr-closing-a-room-deletes-its-future-bookings.md:7`).
- Attendee rows go with the deleted bookings through `ondelete="CASCADE"` (`0003_bookings.py:65-66`), which also depends on `foreign_keys=ON` (`core/db.py:15`).
- Call path:
  - `roombooker/rooms/service.py:215-218 (close_room)` calls `_set_closed(..., is_closed=True)` (`:205-212`). Its only Python-side check is `_require_manager` (`:208`).
    - `roombooker/rooms/store.py:49-50 (set_closed)` runs `UPDATE rooms SET is_closed`, which fires the trigger in the same statement; the commit is at `rooms/service.py:210`.
- The ADR states the intended rule: future bookings are deleted, while in-progress and past ones stay (`adr...md:3`). It also says a booking racing the close cannot survive it. Either the booking commits first and the trigger deletes it, or the close commits first and the overlap guard refuses it with `room_closed` (`adr...md:3`).

**5. "Removed" bookings**
- There is no soft-delete or status column. The `bookings` columns are id, room_id, organiser_id, title, start_at and end_at (`0003_bookings.py:38-57`; `store.py:16-25`).
- A git grep in `roombooker` and `migrations` for `status|cancelled_at|deleted_at|removed` found only HTTP status codes, the iCal `STATUS:CONFIRMED` line and an unrelated web variable. The migrations directory has 0001 to 0004 and none adds such a column (0004 I saw by filename only).
- User cancellation is also a hard delete: `roombooker/bookings/service.py:364-371 (cancel)` calls `store.delete_booking`, and the docstring reads "Cancel (delete, AD-13)". It is allowed only before the booking ends (`:359-360`, `booking_to_cancel`). The current-versus-removed question therefore comes down to whether the row exists.

**Not checked:** the body of `check_slot` and migration 0004's contents. I read 9 of the 15 budgeted files, all through git at 9184f9d; nothing was run.
