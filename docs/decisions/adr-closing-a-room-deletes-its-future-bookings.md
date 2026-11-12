# Closing a room deletes its future bookings, in a database trigger

When an office manager closes a room, its bookings that have not started yet are deleted (cancelled, as AD-13 defines cancelling). A booking already in progress, and past bookings, stay. The user settled what happens to them on 2026-11-12 ("closing a room cancels its future bookings"), which answers the question the architecture had deferred to booking. The deletion is the trigger `rooms_close_cancels_future_bookings` (migration `0003_bookings.py`): an `AFTER UPDATE OF is_closed ON rooms` that runs in the same statement as the close, comparing `start_at` with SQLite's own clock. It is not code in `rooms.service`, because AD-1 lets `bookings.service` depend on `rooms.service` but not the other way round, and a web route calling both services would break AD-1's "web calls only its own module's service". Doing it in the database also means a booking racing the close can't survive it: either it commits first and the trigger deletes it, or the close commits first and AD-4's trigger refuses it as a booking of a closed room. The trade-offs:

- AD-3 names `bookings.service` as the sole writer of `bookings`, and this trigger is a second writer.
- The cancelled bookings are not logged one by one: only the close is logged, by `rooms.service`.
- The deletion uses the database clock rather than `core.time.utc_now()`, so tests can't move it with a fake clock.
- The close confirmation says future bookings will be cancelled, but not how many. Showing the count would need `rooms.web` to ask `bookings.service`.

Revisit if retention (OQ-3) asks for cancelled bookings to be kept, or if `epic-find-and-book` decides to move them to an open room instead.
