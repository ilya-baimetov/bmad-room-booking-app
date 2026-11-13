Digest of `roombooker/templates/`, `roombooker/static/`, `docs/`, `seeds/` and the top-level files, at commit 9184f9d. Everything below was searched through git at that commit. `_bmad-output/`, `_bmad/` and `.claude/` were left out.

**Q1: How a booking stops being active**
- `README.md:43 (Booking a room) @ 9184f9d`: only the person who booked it can **Cancel booking**, and only until the booking ends.
- `README.md:48 (Booking a room) @ 9184f9d`: closing a room cancels its bookings that have not started yet.
- `README.md:76 (Demo bookings) @ 9184f9d`: demo bookings earlier in the week "have already happened and can't be cancelled". So the end time is what makes a booking past.
- `docs/decisions/adr-closing-a-room-deletes-its-future-bookings.md:3 (Closing a room deletes its future bookings, in a database trigger) @ 9184f9d`: cancelling is a delete ("deleted (cancelled, as AD-13 defines cancelling)"). The room-close path is the trigger `rooms_close_cancels_future_bookings`, an `AFTER UPDATE OF is_closed ON rooms` in `0003_bookings.py`.
- `AGENTS.md:24 (Conventions that differ from defaults) @ 9184f9d`: the room-close trigger deletes the future bookings, and Python must not also delete them.
- `roombooker/templates/bookings/details.html:23 (content block) @ 9184f9d`: the confirm form posts to `/bookings/{id}/cancel`. Line 34 shows the Cancel link only when `booking.can_cancel and not has_ended`.
- `roombooker/templates/rooms/_confirm_close_row.html:3 @ 9184f9d`: the close form posts to `/manage-rooms/{id}/close`. Line 5 reads "its future bookings are cancelled".
- `roombooker/templates/rooms/_row.html:8 @ 9184f9d`: the Close and Reopen buttons, chosen by `room.is_closed`.

**Q2: What reads the end time or depends on a booking existing**
- `roombooker/templates/bookings/_item.html:4 @ 9184f9d`: renders `b.start_at`–`b.end_at`. `roombooker/templates/bookings/rooms.html:59 @ 9184f9d` includes it for "Booked then" (`in_slot`), and line 67 for "Your upcoming bookings" (`upcoming`).
- `README.md:33-34 (Booking a room) @ 9184f9d`: "Booked then" is every booking that overlaps the slot. "Your upcoming bookings" is bookings you made that have not ended yet.
- `roombooker/templates/bookings/details.html:10 @ 9184f9d`: renders the end time. Line 32 links the iCal download `/bookings/{id}/calendar.ics`.
- `roombooker/templates/calendar/my_bookings.html:35 @ 9184f9d`: the Day/Week calendar renders `b.end_at`. Lines 51-63 are the feed section (`feed_url`, reset, create).
- `roombooker/templates/calendar/confirm_reset.html:5 @ 9184f9d`: posts the feed reset to `/my-bookings/feed`.
- `README.md:56 (My bookings) @ 9184f9d`: the private `/feeds/<token>.ics` feed.
- `README.md:39-41 (Booking a room) @ 9184f9d`: the start-time and no-overlap rules. Closed rooms can't be booked.
- `AGENTS.md:23 @ 9184f9d`: double bookings are stopped by the `begin_immediate` lock plus the overlap triggers in `0003_bookings.py`. Seed and demo code must also write through `bookings.service`.
- `AGENTS.md:11 @ 9184f9d`: seed and demo data live in `roombooker/seed.py` and `roombooker/demo.py` (outside my area).
- `README.md:63-89 (Demo bookings) @ 9184f9d`: about 60 demo bookings, Monday of this week to Friday of next week. Rerunning skips slots already taken and leaves older weeks in place. The demo needs the build seed's people.
- `seeds/build-people.csv:1 @ 9184f9d`: people only (`email,name,office,office_manager`), no bookings.
- `README.md:102 (Loading people) @ 9184f9d`: people missing from a reload are marked inactive, never deleted. This is a contrast with bookings, which are deleted.
- `roombooker/static/app.css:355 @ 9184f9d`: styles closed-room rows only. Nothing in static reads booking end times.

**Q3: Which bookings the triggers count**
- `docs/decisions/adr-closing-a-room-deletes-its-future-bookings.md:3 @ 9184f9d`: the close trigger deletes only bookings that haven't started yet, comparing `start_at` with SQLite's own clock. Bookings in progress and past bookings stay. A booking racing the close is either deleted by the trigger or refused by "AD-4's trigger" as a booking of a closed room.
- Same file, line 7: the trigger uses the database clock, not `core.time.utc_now()`, so a fake clock in tests can't move it.
- The trigger SQL itself is in `migrations/versions/0003_bookings.py`, outside my area.

**Q4: Why the end is a delete**
- `docs/decisions/adr-closing-a-room-deletes-its-future-bookings.md:3-10 @ 9184f9d`, the stated reasons:
  - The user decided on 2026-11-12 that "closing a room cancels its future bookings".
  - AD-1 lets `bookings` depend on `rooms` but not the reverse, which is why this lives in a trigger and not in `rooms.service`.
- Trade-offs listed there:
  - The trigger is a second writer of `bookings`, against AD-3.
  - Cancelled bookings are not logged one by one; only the close is logged.
  - The close confirmation doesn't say how many bookings it cancels.
- Revisit condition: "if retention (OQ-3) asks for cancelled bookings to be kept". This is the only text that touches delete vs keeping a record.
- `AGENTS.md:29 @ 9184f9d`: `AD-n`/`OQ-n` point to a planning document that no longer exists. The definitions of AD-13 (cancel = delete) and OQ-3 can't be recovered in this repo.

**Q5: How the lifecycle is tested**
- `README.md:114-125 (Tests) @ 9184f9d`: two suites. `tests/*.py` cover rules, pages and the seed command against a temporary database. `tests/e2e/` runs the real app in Chromium (Playwright) at 1280 px and 390 px. `tests/test_demo.py` is named there.
- `pyproject.toml:27 (tool.pytest.ini_options) @ 9184f9d`: `testpaths = ["tests"]`. pytest and pytest-playwright are pinned at lines 18 and 21.
- The ADR's line 7 says tests can't use a fake clock to move the trigger's deletion.

**Searched, nothing found (at 9184f9d)**
- `cancelled_at|status|soft.?delete|deleted_at|archived` in my area: there is no recorded-state representation.
- `end_at` in `roombooker/static/`: no hits.
- Bookings in `seeds/`: none.
- Commit history:
  - The whole repository arrives in one commit, `5f72d52` ("remove BMad files and the walkthrough log"; the earlier history is kept under a `greenfield-done` tag). The ADRs and the close-confirmation wording ("future bookings are cancelled") first appear there.
  - README's "only until it ends" first appears in `5f72d52`, and the line was touched again by `36d0004` and `1f90dba`. The template condition `has_ended` was introduced in `5f72d52`, and its line was touched again by `36d0004` and `1f90dba`.
  - `AGENTS.md:6` says `docs/decisions/` holds "the two surviving design records". No other records show up in the history from `5f72d52` on.
