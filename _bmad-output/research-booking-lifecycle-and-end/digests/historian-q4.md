I couldn't get past the squash. Every line about cancelling and deleting traces to `5f72d52`. The `greenfield-done` tag that holds the earlier history isn't available here: the clone is cut off at that commit, and no tag of that name exists locally. Reading the GitHub origin with `gh api .../tags` needs approval that wasn't given, so I stopped there. So the history shows that cancel deletes the row, but not why that was chosen over keeping it with a recorded status. That rationale lives in "AD-13", in the planning document that no longer exists, and probably in the tag.

**History claims**

- **Load-bearing:** `roombooker/bookings/service.py:364 (cancel)` @ 5f72d52, `roombooker/bookings/store.py:118 (delete_booking)` @ 5f72d52, and `migrations/versions/0003_bookings.py:65-66` (`ondelete="CASCADE"` on `booking_attendees.booking_id`) @ 5f72d52 all arrive in `5f72d52 "chore: remove BMad files and the walkthrough log"`. That commit has no parent here; its message says it is "the same app with no BMad install, planning documents or run log… The greenfield-done tag keeps them." Cancelling is a hard delete, and the attendee rows go with the booking through the cascade.
- `roombooker/bookings/service.py:353-361 (booking_to_cancel)` @ 5f72d52: only the organiser can cancel (`ONLY_ORGANISER`), and only while `end_at > utc_now()` (`ALREADY_ENDED`, line 46). A booking whose `end_at` has passed is never deleted by the app. It stays as history.
- `migrations/versions/0003_bookings.py:54-56` @ 5f72d52: a booking has only `start_at` and `end_at`, plus `ck_bookings_end_after_start`. There is no status or cancelled-at column. Rooms do record a state: `is_closed` Boolean, `0002_rooms.py:31` @ 5f72d52. So bookings are the odd one out in having no recorded end state.
- **Load-bearing:** `migrations/versions/0003_bookings.py:84-95 (rooms_close_cancels_future_bookings)` @ 5f72d52: closing a room runs `DELETE FROM bookings WHERE room_id = NEW.id AND start_at > now`, using SQLite's own clock. So "cancelled" means deleted in this path too.
- `roombooker/bookings/ical.py:52-64 (uid)` @ d7c6ceb comes from `d7c6ceb "feat(calendar): private calendar feed per person, with reset on My bookings"`. The UID scheme it replaced, `booking-{id}@roombooker`, came from `1f90dba "feat(bookings): add "Add to calendar" .ics download to a booking's details page"`. Nothing here was rethought; it adapts to the existing delete model. `bookings.id` is a plain `Integer primary_key` with no AUTOINCREMENT (`0003_bookings.py:40`), so SQLite can reuse the id after a delete. It is the only cited line not from the squash.

No pull requests: every commit cited is either the parentless squash or a direct commit on the local `my-changes` branch, and I made no `gh` lookups.

**Rationale found**

- `docs/decisions/adr-closing-a-room-deletes-its-future-bookings.md` (in 5f72d52):
  - "its bookings that have not started yet are deleted (cancelled, as AD-13 defines cancelling)". It confirms AD-13 equates cancel with delete but doesn't say why.
  - The user settled it on 2026-11-12: "closing a room cancels its future bookings".
  - The delete lives in a trigger, not in `rooms.service`, because of the one-way service dependencies ("AD-1"). It also wins any race: a booking that commits first gets deleted, and one that commits after the close is refused by the closed-room trigger ("AD-4").
  - Trade-offs it accepts: a second writer of `bookings` (against "AD-3"); "The cancelled bookings are not logged one by one: only the close is logged"; it uses the database clock, so a fake clock in tests can't move it.
  - Revisit condition: "if retention (OQ-3) asks for cancelled bookings to be kept". This is the only text in the repo that admits the cancelled-status alternative exists, and it marks that alternative as deferred to an open question, not rejected.
- `ical.py:53-54` docstring and the d7c6ceb message: the hash covers room, times and title "so a booking id SQLite reuses after a delete is a new event, never an update of the old."
- `store.py:119` and `service.py:365` cite "AD-13" and nothing more.

**Decisions shown being made**

- **Closing a room deletes its future bookings, in a trigger rather than Python service code.** This was chosen over code in `rooms.service` or a route calling both services, because of the dependency direction and to win races. Recorded in 5f72d52, in the ADR above.
- **Event UIDs carry a content hash** (`d7c6ceb`). This was chosen over the bare `booking-{id}` UID from `1f90dba`, because a deleted booking's id can be reused. This decision accepts the delete model; it doesn't revisit it.
- **Cancel as delete, not as a recorded state (AD-13).** The history doesn't show this decision being made. It predates the squash and isn't recoverable here.

**Budget:** 3 of 10 commits followed (`5f72d52`, `1f90dba`, `d7c6ceb`); `36d0004` touched `service.py` but none of the cited lines. History stopped at the squash, so the remaining budget went unused. What's left is to read the `greenfield-done` tag and find the commits that introduced `cancel`, `delete_booking`, the cascade and the close trigger, plus the planning-doc text for AD-13 and OQ-3. That needs either a fetch of the tag, which writes to `.git`, or approval for `gh api` reads on the origin repository.
