---
epic: epic-offices-and-rooms
date: 2026-11-12
verdict: accepted-with-open-items
criteria: declared
headless: false
---

# Retrospective — epic-offices-and-rooms

## Epic summary

- Epic: `epic-offices-and-rooms`, "Office managers keep their rooms current" (`epic-offices-and-rooms.md`, `status: done`, closed in `696ebff`).
- Tickets, in build order: 1.1 Pick and switch your name, end to end (`done`); 1.2 Office managers manage their office's rooms (`done`).
- `pending_tickets`: none. Tickets at `built`: none.
- Going-in concerns from the user: none.

### Plan ranges

| Ticket | Plan | baseline_revision | Range | Commits |
|---|---|---|---|---|
| 1.1 | `tickets/story-pick-and-switch-your-name-end-to-end-plan.md` | `8a7db0e` | `8a7db0e..22bbc6a` (recorded) | `cf77262` feat, `22bbc6a` mark done |
| 1.2 | `tickets/story-office-managers-manage-their-office-s-rooms-plan.md` | `22bbc6a` | `22bbc6a..696ebff` (HEAD, inferred) | `d2a5b1f` feat, `b28a00b` mark done, `696ebff` epic close (planning files only) |

Neither range has merges (`merge_count` 0). None of the epic's code is on `main`. `main` is still at `8a7db0e`, and the work sits on stacked branches, `story-1-1-pick-your-name` then `story-1-2-manage-rooms` (`git log --decorate`).

### Evidence inventory

| Evidence | Status |
|---|---|
| Epic file: Requirements R1–R9 and Done when | Read in full. Criteria are **declared**. |
| Ticket entries (`tickets.toml`, `find 1.1`, `find 1.2`) | Read. Both carry a description and a verify step; neither was pulled. |
| Story files | None. Neither ticket was pulled (`story_file: null`), so the entries are the spec. |
| Plans | Both read in full: frozen intent, Code Map, Implementation Notes, Review Triage Log, Design Notes, Verification. |
| Dated `## Code Review` blocks | Absent from both plans. Review is recorded in the Review Triage Log: quick lens only, `review_source: pinned`. |
| Plan Change Log | Present and empty in both plans. |
| `git_evidence.py` | Run once per range. |
| Run folders (`<type>-*/`) | None in the epic folder. |
| Companions | Architecture spine opened for AD-1 (with its diagram) and AD-12 only. |
| Epic `.memlog.md` | Read. |
| Previous retrospective | None. This is the first epic in `epics` order. |
| Session logs | Found in `~/.claude/projects/-home-claude-runs-room-booker/`: `79383f16` (build 1.1), `6fb5ad90` (mark 1.1 done), `cad2024f` (build 1.2), `30bc71ce` (mark 1.2 done), `4c3fae67` (epic close). Main-thread messages read. The build subagent transcripts were not inspected. |

## Findings

Each ID is cited in Action items. Each disposition gives what to do about this instance, then what would prevent the next one.

### Behavior and spec reconciliation

**F1. A stale cookie on a POST-only route ends on a JSON 405 page after re-picking (R2).** Story 1.1's `NeedsPerson` sets `next` to the request path for every method (`roombooker/core/identity.py:63`). Story 1.2 then added POST-only routes: `POST /manage-rooms/{id}` and `POST /manage-rooms/{id}/reopen` (`roombooker/rooms/web.py:157,220`). When the cookie is missing, unknown or inactive at the moment of a write, the person goes to `/pick-name?next=/manage-rooms/1/reopen`. After they pick, the browser GETs that path and receives `405 {"detail":"Method Not Allowed"}`. The behavior check below reproduced this for both routes, and for htmx, which gets `HX-Redirect=/pick-name?next=/manage-rooms/1/reopen`. R2 promises a return "to the page asked for". This is a seam no single session saw: the 1.1 review never saw POST routes, and the 1.2 review never revisited the identity redirect. Sources: bmad-review adversarial, edge-case and verification-gap lenses; behavior check.
- Disposition: **fix now** (small; see A1).
- Prevent: when a story adds routes behind `CurrentPerson`, its verify step includes the stale-cookie round trip.

**F2. The framework's 404, 405 and 422 responses are JSON.** `roombooker/app.py:41-42` registers handlers only for `NeedsPerson` and `DomainError`. Starlette's HTTP errors and `RequestValidationError` fall through to FastAPI's JSON defaults, as F1 shows. Story 1.1 already patched one instance by hand (plan 1, Review Triage #4: "`gone=x` returns a JSON 422"), so this has now come up in both stories. It conflicts with plan 1's "Never: a JSON API" and with AD-12's one error path. Source: adversarial lens; plan 1 Review Triage Log #4.
- Disposition: **fix now** together with F1 (A1).
- Prevent: add a core rule that every response is HTML (see A5).

**F3. The 1.1 switch behavior changed under `/manage-rooms`.** From Manage rooms, the switch link now goes through `/` (`roombooker/templates/base.html:22`), not back to the same page as 1.1's AC2 said. Story 1.2's review made this change deliberately (plan 2, Review Triage #1) so that switching to someone who doesn't manage that office doesn't land on a 403. It is tested at `tests/test_rooms.py:97`.
- Disposition: **accept**. This is a recorded deviation, so later retros should not flag it again.
- Prevent: nothing.

**F4. Known issue: an htmx add discards a row open for Edit or close confirmation.** See `roombooker/rooms/web.py:132-143`. Plan 2 Review Triage #3 rejected it as unlikely, and the epic Notes list it as "Known issue, not ticketed".
- Disposition: **defer**. The epic Notes carry enough context to pick it up later (A6).
- Prevent: nothing.

Everything else checked out. The epic file's R1, R3–R9, its constraints (RULE-4, RULE-6 logging, RULE-9 widths) and each Done when line match the as-built code, and the behavior check and test suite confirm it. R7's limits (50 characters; capacity 1–200) match `roombooker/rooms/service.py:21-23`, after the epic file was reconciled in `696ebff`.

### Architecture delta

The import graph was derived from `roombooker/**` imports with an inline grep; no dependency tool was run.

**F5. `core` depends upward on `people.service`, against the spine's diagram.** The AD-1 diagram shows `core` "used by all" and says dependencies "never point upward or in a cycle". In the code:
- `roombooker/core/identity.py:17-18` imports `people.service`.
- `roombooker/core/errors.py:32-33` lazily imports `core.identity`, so `rooms.service → core.errors → core.identity → people.service`.
- `roombooker/people/service.py:3` guards the cycle by convention only: "Must never import `core.identity`".

Plan 1's Code Map chose this on purpose ("`identity.py` imports `people.service`"), but the spine was never updated to match.
- Disposition: **accept** the structure, and **reconcile the spine**: state that `core.identity` sits above `people.service` (A4).
- Prevent: a plan that departs from a spine diagram should record a spine change in its Plan Change Log.

**F6. `_person_for_top_bar` runs its own session outside dependency injection.** It drives `get_session()` by hand and re-runs `current_person` in a second session, which bypasses FastAPI dependency overrides and adds a second lookup per refusal (`roombooker/core/errors.py:26-41`). Source: adversarial lens.
- Disposition: **defer**, folded into the core refactor (A2).

No layering violations between stores: each store is imported only by its own service, plus `people.store` by the seed CLI.

### Duplication map

**F7. Request helpers are re-solved in each web module.**
- The `HX-Request` check appears four times: `core/identity.py:96`, `core/errors.py:46`, `people/web.py:47` and `rooms/web.py:34`.
- `_render` appears twice and the copies differ: `people/web.py:21` doesn't set `Vary`, while `rooms/web.py:38` does.
- The `DbSession` alias is defined twice: `people/web.py:18` and `rooms/web.py:22`.

`bookings.web` and `calendar.web` are next, and each will copy one of these. Source: adversarial lens.
- Disposition: **defer** to a small refactor before epic-find-and-book's first web story (A2).
- Prevent: the epic declined a refactor sweep (epic Notes, "no refactor sweep … since the epic has two entries"). This finding is what such a sweep would have caught.

**F8. Two conventions guard against SQLite integer overflow on ids.** `core/identity.py:60` and `people/web.py:63` accept at most 18 digits, which also refuses valid 19-digit ids. `rooms/service.py:83` bounds by value, `<= 2**63-1`.
- Disposition: **defer** into A2, as one `parse_id` in core.

### Pattern divergence

**F9. `NotAllowed` in core has a rooms-specific default message.** `roombooker/core/errors.py:21-23` defaults to "Only office managers can manage rooms.". epic-find-and-book will raise `NotAllowed` for RULE-3 and show that wording unless every raise passes its own message.
- Disposition: **fix in A2**, before epic-find-and-book raises it.

**F10. The `rooms` query table leaves out its foreign key.** `roombooker/rooms/store.py:19` has no ForeignKey (only a comment), while `people/store.py:40` declares one.
- Disposition: **accept**. It is cosmetic, because the migration enforces the key.

### God-class and size growth

Checked, and clean. The largest Python files are `rooms/web.py` (224 lines) and `rooms/service.py` (210). `static/app.css` reached 508 lines over the two stories (+245, +263). It is still a single stylesheet; watch it as find-and-book and calendar add screens. No `binary_revisions`, and no merges went unmeasured.

### Diff-scope review (bmad-review: adversarial, edge-case, verification-gap)

The review ran over `8a7db0e..696ebff` for code only (excluding `_bmad-output/`, `uv.lock` and the vendored htmx), weighting the seams between the two stories. The three lenses ran **inline, one after another, not as parallel subagents**. That narrows the review: one reviewer played each lens, so independent disagreement between lenses was lost. Raw findings: `/tmp/claude-0/-home-claude-runs-room-booker/9e7dff7d-2e77-46a5-aab9-4e990d3104df/scratchpad/epic-review-findings.json` (17 entries). They are already folded into F1, F2 and F5–F10 above. The ones not covered there:

- **F11.** The seed matches office names case-sensitively (`roombooker/seed.py:60`, `people/store.py:98-105`). An HR file that says "london" would create a fourth office and move people and their manager rights away from London's rooms. Disposition: **defer to epic-deployment**, which owns loading HR's list (A7).
- **F12.** The case-insensitive room-name rule lives only in Python, while the database constraint is exact-match (`rooms/service.py:89-97`, `0002_rooms.py:33`), so two concurrent adds with different case could both commit. Disposition: **accept**. Plan 2's Design Notes chose this, and one office manager per office makes concurrency negligible.
- **F13.** htmx `responseHandling` swaps only 2xx, 403, 404 and 422 (`base.html:6`). A 400, 405 or 500 during an htmx Save or Close shows nothing. Disposition: **fix with A1**.
- **F14.** A name made only of zero-width or control characters passes the non-empty check (`rooms/service.py:107-111`). Disposition: **accept**. It is low-value.
- **F15 (verification gap).** Nothing asserts that the 403 page keeps the current name and Switch link (`core/errors.py:61`). The tests check only `#announce` and the absence of tabs (`tests/test_rooms.py:276-280`, `tests/e2e/test_manage_rooms.py:176-181`). Disposition: **fix with A1**, as one assertion.
- **F16 (verification gap).** No test follows `next` after a non-GET guarded request (`tests/test_people_web.py:114-123` is GET-only). This is the test for F1 (A1).

Claims check: the commit claims that the `person_id` cookie is read only by `core.current_person` (`cf77262`) holds; `request.cookies` appears only at `core/identity.py:58`. The claim of "the AD-12 error handler" (`d2a5b1f`) holds for domain errors only, which is F2.

### Process lessons (session logs and plans)

- **P1. Both plans ran over the 1,600-token plan target:** about 2,370 tokens (`79383f16`, message 138) and about 2,900 (`cad2024f`, message 154). The user chose to keep each one whole. Story 1.2's build went through anyway, with three review patches and no loopback, so the epic Notes' fallback split wasn't needed. Lesson: none required. The target flagged the right story, and the check worked as intended.
- **P2. Nothing was merged to `main`.** The 1.2 session found story 1 unmerged and recommended stacking a branch (`cad2024f`, message 95). The epic then closed with all of its code off `main`. epic-deployment depends on "the app running locally" (`tickets.toml` `after`) and will want a stable base. Lesson: closing an epic should include merging its branches, or recording why not (A3).
- **P3. Each story had only the quick review lens** (`lenses_ran: [quick]`, `review_source: pinned`). It caught real bugs in each story: the 500 on an oversized id, the accented-name search, and the switch-to-403. But no lens looks across stories, which is how F1 got through. Lesson: for a medium-risk story that builds on an earlier story's core, add a check of how the two fit together to its verify step, or keep this retro's cross-story pass as the gate (A5).

## Behavior verification

I ran the real app factory on a scratch database (Alembic to head, build seed loaded) through `TestClient`, with a script at `/tmp/claude-0/-home-claude-runs-room-booker/9e7dff7d-2e77-46a5-aab9-4e990d3104df/scratchpad/behavior_check.py`. I didn't run a live uvicorn and curl walk because that needed a permission prompt. What I observed:

- R1, R2, R9: no cookie on `/` gives 303 to `/pick-name?next=/`. Anna's pick gives 303 to `/`, which sends her on to `/manage-rooms`. Hannah gets "Booking opens soon." with no tabs.
- R3–R5 with plain forms: add, edit, close and reopen each return 303 with the right notice. The table shows `Closed` after close. The final database row is `('Boardroom', 10, 0)`.
- R7: capacity 0 returns 422 with "Capacity must be a whole number from 1 to 200.". `BOARDROOM` returns 422 with "already has a room called Boardroom." and the form keeps the typed value.
- R6: Hannah on `/manage-rooms` and Joanne closing a London room each get 403, and the room stays open.
- RULE-6: log lines name `person_id` for each pick, add, edit, close, reopen and refusal.
- Where the stories meet: **F1 reproduced.** Re-picking after a stale-cookie POST to `/manage-rooms/1` or `/manage-rooms/1/reopen` ends on a JSON 405. `/close` happens to work because it has a GET confirmation route.
- Suite: `uv run pytest`: **80 passed** (e2e at 1280 and 390 widths, Chromium), with 2 deprecation warnings (httpx in TestClient; a session-scoped fixture written as an instance method).

I didn't visually check the phone layout myself. The epic Notes record that the user walked both stories at both widths.

## Previous-retro follow-through

Nothing to follow through: there is no previous retrospective file. This is the first epic in `epics` order.

## Action items

All of these are proposed. Code fixes go through the normal dev loop (`bmad-build`), and ticket or spine edits through Sofia (`bmad-agent-po`) or Winston (`bmad-agent-architect`).

| # | Action | Findings | Owner | Kind |
|---|---|---|---|---|
| A1 | Bug ticket: (a) `NeedsPerson` uses the GET page (`HX-Current-URL`, else `/`) for non-GET requests; (b) HTML handlers for Starlette HTTP errors and `RequestValidationError`; (c) an htmx catch-all so 400, 405 and 500 errors show in `#announce`; (d) tests: follow `next` after a stale-cookie POST to `/manage-rooms/{id}/reopen` and expect a 200 HTML page, and assert the name in the 403 page's top bar. | F1, F2, F13, F15, F16 | Sofia files it; Amelia builds it | remediation |
| A2 | Small refactor story before epic-find-and-book's first web story: move `is_htmx`, `render` (always with `Vary`), `DbSession` and `parse_id` into a core module; give `NotAllowed` a neutral default and move the rooms wording to `rooms.service`; have `current_person` store the `Person` on `request.state` so the error handler stops opening a second session. | F6, F7, F8, F9 | Sofia (ticket in epic-find-and-book); Amelia | remediation |
| A3 | Merge `story-1-2-manage-rooms` into `main` (it includes 1.1), or record why it stays off `main`, before epic-deployment starts. | P2 | User | process |
| A4 | Spine reconciliation: AD-1's diagram should show that `core.identity` depends on `people.service`, and that `core.errors` reads identity only for the top bar. | F5 | Winston (`bmad-agent-architect`), user approves | spec reconciliation |
| A5 | Process: when a story adds routes or handlers behind `CurrentPerson` or the core error path, its verify step includes the stale-cookie round trip and a check that every response is HTML. | F1, F2, P3 | Sofia (story template and verify wording) | process |
| A6 | Decide whether F4 (htmx add discards an open edit row) becomes a backlog bug or stays as a known issue. | F4 | User with Sofia | triage |
| A7 | Carry F11 (office names matched by case) into epic-deployment's "load HR's list" work as a requirement. | F11 | Sofia | spec reconciliation |

## Decision records

The test was applied to each plan's frozen block, Design Notes and Implementation Notes. The repository has no existing `adr-*.md` files or decisions folder.

| Proposed record | Source | Status |
|---|---|---|
| `docs/decisions/adr-case-insensitive-matching-in-python-not-sqlite.md`: names are compared with Python `casefold()`, not SQLite `lower()`. This covers people search and the room-name duplicate check, with the exact-match unique constraint kept as a backstop. | Plan 2 Design Notes ("A duplicate name is checked in the service with `casefold()`…"); plan 1 Review Triage #3; commits `cf77262`, `d2a5b1f` | **Approved by the user 2026-11-12; written** to `docs/decisions/adr-case-insensitive-matching-in-python-not-sqlite.md` (not committed) |

Considered and not proposed: the htmx `responseHandling` config and the server-rendered close confirmation are easy to reverse. The `person_id` cookie, the layering and the error path are already recorded in the architecture spine (AD-6, AD-1, AD-12). "Rooms are never deleted" comes from the epic's own decision record, not from a plan trade-off.

## Acceptance verdict

**accepted-with-open-items**, with criteria **declared**. The user accepted this verdict on 2026-11-12 without overriding it.

Every Done when line is shown by the evidence:
- Picking and remembering a name: e2e `test_pick_name_shows_in_top_bar_after_reload`, and the behavior check.
- Office-manager-only add, edit, close and reopen, with refusals including direct requests: the behavior check, `test_refused_unless_managing_the_office`, and e2e `test_office_manager_of_another_office_is_refused`.
- Closed rooms shown as Closed, and invalid or duplicate rooms refused: the behavior check.
- Seed in one command, with reloads keeping ids: `tests/test_seed.py`, and e2e `test_reload_without_person_sends_them_to_pick_your_name`.
- Integrated verification at both widths: 80 passed.

R1 and R3–R9 are met. R2 is met on every GET page. Its "returns to the page asked for" fails on a narrow path, a stale cookie during a write (F1), and that path is open as A1; it does not block. No tickets are unfinished. The open items, in order:
- A1: fix now.
- A2: before epic-find-and-book.
- A3: before epic-deployment.

## Open questions

- Should F1 and F2 (A1) be fixed before epic-deployment, or folded into epic-find-and-book's first story? Fixing them first keeps the epic's R2 claim true on what gets deployed.
- Was leaving the code off `main` deliberate (A3)? The answer decides which branch epic-deployment builds from.
