---
title: 'Each person subscribes to a private feed of their bookings and can reset its address'
type: feature
ticket: '2'
created: '2026-11-13'
status: done
baseline_revision: 'ac3858abe891c35891774ecff1e149edd162bd80'
route: full
route_source: auto
risk: high
review: quick
review_source: pinned
lenses_ran: [quick]
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** A downloaded .ics file is a snapshot, so people's calendars drift from the room booker as bookings are made, cancelled or wiped by a room closing.

**Approach:** Each person gets a secret feed address (`/feeds/<token>.ics`), shown on My bookings with a reset. Calendar apps fetch it with no cookie and get the person's organised and attended bookings that end after 30 days ago, formatted by story 1's `ical.calendar`.

## Boundaries & Constraints

**Always:** The token is `secrets.token_urlsafe(32)`, stored in a new nullable, unique `people.feed_token` column (migration `0004`), and written only through `people.service`. The feed resolves its person from the token alone, never from `CurrentPerson`, and an unknown, malformed, replaced or inactive person's token gets a plain-text 404 with no bookings. Every other new route uses `CurrentPerson`, and My bookings shows only the viewer's own address. Feed response: `text/calendar; charset=utf-8`, `Cache-Control: private, no-cache`, calendar name `Room bookings`, refresh hint one hour. The address is absolute, built from the request's base URL. A reset is a POST with redirect-after-post, behind a confirmation like Cancel booking, and works as a full page load. Layering: `calendar.web` → `calendar.service` → `bookings.service` / `people.service`.

**Never:** No reads from or writes to any calendar app, no Microsoft or Google calls, no ATTENDEE/ORGANIZER lines, no `datetime.now()`, no SQL `lower()`. No Python deletion of bookings on room close (the trigger does it). No change to how bookings are made, the overlap triggers, or what My bookings lists. No room- or office-wide feeds.

**Decisions:**
- (user, 2026-11-13) Event UIDs are `booking-<id>-<first 8 hex of sha256 over room id, start, end, title>@roombooker`, written by the shared `ical` formatter for both the feed and story 1's download. A reused booking id is then a new event, not a stale update. This renegotiates story 1's UID line.
- (user, 2026-11-13) An address exists only once the person presses Create feed address on My bookings. GET pages never write.
- (user, 2026-11-13) The plan stays whole at ~1,800 tokens: it has one goal.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Subscribed fetch | Valid token, no cookie; person organises A, attends B, neither on C; D ended 31 days ago | 200, events A and B only, UTC times | No error expected |
| Cancelled | A cancelled, then fetch | A gone | No error expected |
| Room closed | A's room closed via `rooms.service`, then fetch | A gone | No error expected |
| Reset | Old token after reset | 404; new token serves the bookings | Plain-text 404 |
| Unknown / malformed | Random 43-char token, `abc`, `../x` | 404 | Plain-text 404, no DB write |
| Inactive | Person marked inactive by the seed | 404 | Plain-text 404 |
| No address yet | Person never created one | My bookings offers Create feed address; no token stored until then | — |
| No cookie on My bookings / reset | Fresh browser | Existing Pick your name flow | Existing redirect |

</frozen-after-approval>

## Code Map

- `migrations/versions/0004_people_feed_token.py` -- new: `op.add_column("people", feed_token String nullable)` plus unique index `uq_people_feed_token` (SQLite allows many NULLs). Follow `0001` naming.
- `roombooker/people/store.py` -- add the `feed_token` column to `people`; add `set_feed_token(session, person_id, token)` and `active_by_feed_token(session, token) -> Row | None` (joins offices like `_person_select`, `active` true). `load_people` must not touch the column.
- `roombooker/people/service.py` -- `feed_token(session, person) -> str | None`, `new_feed_token(session, person) -> str` (creates or replaces, commits), `person_for_feed_token(session, token) -> Person | None`. It must not import `core.identity`.
- `roombooker/bookings/ical.py` -- `calendar(events, stamp, name: str | None = None)`. With a name it adds `X-WR-CALNAME`, `REFRESH-INTERVAL;VALUE=DURATION:PT1H` and `X-PUBLISHED-TTL:PT1H` after METHOD. Without a name the calendar lines match story 1's output. `_event`'s UID changes to the content-hashed form (Decisions); update the UID assertions in `tests/test_ical.py` / `tests/test_bookings.py`.
- `roombooker/bookings/service.py` -- `feed_calendar(session, person) -> str`: `bookings_for_person(person, utc_now() - 30 days, datetime(9999,12,31,23,59,tzinfo=UTC))` → `ical.calendar(..., name="Room bookings")`.
- `roombooker/calendar/service.py` -- `feed(session, token) -> str | None`, `feed_address_token(session, person)`, `reset_feed(session, person)`. Calls `people.service` and `bookings.service` only.
- `roombooker/calendar/web.py` -- `GET/HEAD /feeds/{token}.ics`. Reject a token that isn't 43 chars of `[A-Za-z0-9_-]` before any lookup. `GET /my-bookings/feed/reset` (confirm page) and `POST /my-bookings/feed` (create or reset), then 303 to `/my-bookings?notice=feed`. `my_bookings` passes `feed_url` (`str(request.base_url).rstrip("/") + f"/feeds/{token}.ics"`) or None.
- `roombooker/templates/calendar/my_bookings.html` -- a "Calendar feed" section below the calendar: a read-only, select-on-focus input holding the address, a short hint (paste into Outlook / Google / Apple "subscribe from URL"; changes show after the app refreshes), and a Reset link. With no address, a Create feed address form button. Notice text from a `NOTICES` map like `bookings/web.py:43`.
- `roombooker/templates/calendar/confirm_reset.html` -- new, mirrors the cancel confirmation in `bookings/details.html:22-29`.
- Tests reuse fixtures from `tests/test_bookings.py` the way `tests/test_calendar.py:9` does (`act`, `room`, `book`, `ids`, `insert_booking`); `client` has `follow_redirects=False`.

## Tasks & Acceptance

**Execution:**
- [x] `migrations/versions/0004_people_feed_token.py` -- add column + unique index, with a downgrade -- schema changes only via Alembic
- [x] `roombooker/people/store.py`, `roombooker/people/service.py` -- token column, lookups, create/replace -- people owns the secret
- [x] `roombooker/bookings/ical.py`, `roombooker/bookings/service.py` -- named calendar + `feed_calendar` -- reuse story 1's formatter
- [x] `roombooker/calendar/service.py`, `roombooker/calendar/web.py` -- feed, confirm and reset routes; `feed_url` on My bookings
- [x] `roombooker/templates/calendar/my_bookings.html`, `confirm_reset.html` -- feed section and confirmation
- [x] `tests/test_feed.py` -- one test per matrix row through the HTTP client, plus: My bookings shows only the viewer's address; a reused booking id gets a different UID; the download differs from story 1 only in the UID; migration upgrade/downgrade round trip
- [x] `README.md` -- one paragraph: feed addresses come from the request's host, so run uvicorn with `--proxy-headers` behind a TLS proxy

**Acceptance Criteria:**
- Given a person on My bookings, when they create an address and paste it into a calendar app's subscribe-from-URL, then the app shows their organised and attended bookings at the right UK time.
- Given a subscribed calendar, when a booking is made, cancelled, or removed by a room closing, then the next refresh shows the change (manual check in Outlook, Google Calendar and Apple Calendar, `hitl`; it needs the app reachable from those services, an open question on the initiative).

## Implementation Notes

- Migration `0004`'s downgrade is a plain `ALTER TABLE ... DROP COLUMN`, not a batch rebuild, so `people` (which bookings reference) is never dropped and recreated.
- The feed route is `/feeds/{name:path}`, so an encoded `..%2F` reaches the handler and gets the plain 404. A literal `../` is resolved by clients before the request is sent, and gets the app's default 404.
- After review, the POST takes `replace=1` (sent only by the confirmation). A Create pressed while an address exists goes to the confirmation, and the notices are now `feed-created` and `feed-reset`.
- `uv run pytest --ignore=tests/e2e`: 132 passed; `uv run pytest tests/e2e`: 21 passed. The migration round trip is covered by `test_migration_downgrade_and_upgrade_round_trip`, and the implementer ran it on the CLI against seeded demo data. The three-app subscription check (`hitl`) is still to do.

## Plan Change Log

## Review Triage Log

Pass 1 (quick): high 0, medium 1, low 3, false 0, maybe-false 0.

| # | Finding | Verdict | Route | Evidence / action |
|---|---------|---------|-------|-------------------|
| 1 | POST `/my-bookings/feed` with no cookie → Pick your name → GET on a POST-only path → 405 | low | reject (+ defer pattern) | Confirmed: `NeedsPerson` keeps the path, and there's no GET route for it. It only happens when the cookie is lost between loading the page and the click, and the fix adds a route. The same flaw already exists for `POST /bookings`, `/manage-rooms/{id}` and `/reopen`, so the app-wide pattern is deferred. |
| 2 | Create and Reset share one POST, so a stale Create page replaces a live address without the confirmation | medium | patch | Confirmed: the handler called `new_feed_token` unconditionally. Against the Always rule "reset behind a confirmation". Fixed: the confirmation sends `replace=1`, and a Create while an address exists redirects to the confirmation without writing. Test `test_stale_create_goes_to_the_confirmation_without_replacing`. |
| 3 | First creation's notice says an earlier address stopped working | low | patch (grouped with 2) | Same root cause: the endpoint couldn't tell create from reset. Now `feed-created` and `feed-reset`, each with accurate text, both tested. |
| 4 | Test case `..%2F` + 39 `a` is 42 chars, so it's rejected on length, not on its characters as the comment says | low | patch | Confirmed: ASGI paths are percent-decoded. Changed to 40 `a`, giving 43 decoded characters. |

## Design Notes

404 rather than an empty calendar for a dead token: the app reports an error, so the person knows to resubscribe, and nothing confirms that a token ever existed. The token is stored as plain text because R6 needs it shown again. 256 bits of randomness makes guessing hopeless (R4). A reactivated person's old token works again; that matches "inactive stops returning bookings" without adding state.

## Verification

**Commands:**
- `uv run pytest --ignore=tests/e2e` -- expected: all pass
- `uv run pytest tests/e2e` -- expected: all pass (My bookings still renders)
- `uv run alembic upgrade head && uv run alembic downgrade 0003 && uv run alembic upgrade head` on a scratch `ROOMBOOKER_DB_PATH` -- expected: clean

**Manual checks (if no CLI):**
- Subscribe in Outlook, Google Calendar and Apple Calendar. Make, cancel, and close-room a booking, and check each refresh. Do one booking in GMT and one in BST.
