---
type: epic
title: Office managers keep their rooms current
parent: initiative-company-room-booking
covers: [R1, R2, R3, R4, R5]
sources:
  - _bmad-output/initiative-company-room-booking/initiative-company-room-booking.md
companions:
  - _bmad-output/initiative-company-room-booking/architecture-company-room-booking/architecture-company-room-booking.md
  - _bmad-output/initiative-company-room-booking/ux-company-room-booking/EXPERIENCE.md
  - _bmad-output/initiative-company-room-booking/ux-company-room-booking/DESIGN.md
after: []
status: done
refined: true
risk: medium
---

# Office managers keep their rooms current

## Description

The app's first release, running on the user's computer: anyone picks their name from the seeded people, and an office manager adds, edits, closes and reopens their own office's rooms. It lays the ground the later epics build on: the scaffold, the database, seed loading, the app shell, the type-ahead people picker, the current person and the office-manager check. Putting it on the company host is epic-deployment's.

## Outcome

Office managers in London, Manchester and Leeds can keep an accurate room list in the app, shown on the user's computer at laptop and phone widths, so the rooms exist before anyone books (initiative R1 to R5).

## Requirements

- R1 (parent R1): A person picks their name from the seeded active people by typing part of it, then uses the app as that person; their name shows in the top bar on every page.
- R2 (parent R2): A person switches name from the top bar at any time; the device remembers the picked name until they switch; a missing, unknown or inactive name opens Pick your name and then returns to the page asked for.
- R3 (parent R3; user 2026-11-12): An office manager adds a room to their office with a name and a capacity; it appears in their rooms table as Open.
- R4 (parent R4; user 2026-11-12): An office manager edits the name and capacity of a room in their office; the rooms table shows the new values.
- R5 (parent R5): An office manager closes and reopens a room in their office; a closed room shows as Closed and a reopened one as Open.
- R6 (parent RULE-4; experience State Patterns): Anyone who is not an office manager of a room's office is refused adding, editing, closing or reopening its rooms, even by a direct request; the Manage rooms tab shows only to office managers, and a direct link shows "Only office managers can manage rooms."
- R7 (user 2026-11-12; story 2 limits): A room with an empty name or one over 50 characters, a capacity that is not a whole number from 1 to 200, or a name already used in its office is refused with the reason, and the form keeps its values.
- R8 (parent Constraints, seed file; user 2026-11-12): One command loads offices, people, home offices and office-manager marks from a CSV with columns `email, name, office, office_manager`; a reload updates people matched on email and marks anyone missing from it inactive, keeping their id.
- R9 (user 2026-11-12): Tabs show only for screens that exist; until epic-find-and-book ships Rooms, after picking a name an office manager lands on Manage rooms and anyone else on a page with their name and "Booking opens soon."

## Constraints

- Parent RULE-4: Only office managers add, edit, close or reopen rooms, and only in their home office.
- Parent RULE-6: No accounts or passwords; anyone can pick anyone's name; every change logs the acting person, as evidence for SM-5.
- Parent RULE-7: Python, FastAPI and SQLite; built and tested on the user's computer; hosting per architecture AD-11 is epic-deployment's.
- Parent RULE-9: Every feature works in a browser on laptop and phone; Manage rooms is laptop-first and a simple list on phone.
- User, 2026-11-12: Integrated verification runs with Playwright for Python at laptop and phone widths.

## Done when

- On the user's computer, a person picks their name from the seeded people, the app shows it throughout, and the device remembers it until they switch.
- An office manager adds, edits, closes and reopens rooms in their own office only; anyone else is refused, including by a direct request.
- A closed room shows as Closed; invalid or duplicate rooms are refused with the reason.
- Offices, people, home offices and office-manager marks load from the seed file with one command, and a reload keeps everyone's id.
- Integrated verification passes on the user's computer, at laptop and phone widths.

## Boundaries

- Not here: the deploy bundle, standing the app up on the company host, CI, integrated verification on the deployed app, loading HR's list, and office managers checking their rooms on the live app; all epic-deployment.
- Not here: finding free rooms, bookings, refusing bookings of a closed room, the future-booking count when closing, or what happens to those bookings; all epic-find-and-book.
- Not here: the calendar; epic-my-calendar.
- Not here: editing people or offices inside the app (initiative Boundaries).
- Owns for later epics: the shell (top bar with the current name, tabs, DESIGN.md tokens), the people picker, the current person and the office-manager check.

## References

- parent — _bmad-output/initiative-company-room-booking/initiative-company-room-booking.md, section Requirements (R1 to R5) and Constraints
- architecture — _bmad-output/initiative-company-room-booking/architecture-company-room-booking/architecture-company-room-booking.md, AD-1, AD-2, AD-3, AD-6, AD-7, AD-9, AD-10, AD-12, Consistency Conventions, Stack, Structural Seed
- experience — _bmad-output/initiative-company-room-booking/ux-company-room-booking/EXPERIENCE.md, Name picker, Rooms table, State Patterns, Responsive & Platform, UJ-4
- design — _bmad-output/initiative-company-room-booking/ux-company-room-booking/DESIGN.md

## Notes

- Assumption: People are matched on email, and anyone missing from a reload is marked inactive, not deleted (architecture AD-9).
- Decision: 2026-11-12, user: opening epic, because nothing can be booked until rooms exist; the platform baseline is its first stories.
- Decision: 2026-11-12, user: deployment splits into a deploy bundle (Dockerfile, Caddyfile, Litestream config) that runs locally, unblocked, and standing it up on the company host, a person's step blocked on OQ-4. Both now belong to epic-deployment.
- Decision: 2026-11-12, user: seed CSV columns `email, name, office, office_manager`, office by name; a made-up build seed of about 30 people across the three offices.
- Decision: 2026-11-12, user: a room is a name and a capacity (whole number, 1 or more), names unique within an office; Edit changes only name and capacity, status changes only through Close and Reopen.
- Decision: 2026-11-12, user: tabs appear only once their screen exists; the "Booking opens soon." landing for people who are not office managers is replaced by epic-find-and-book's Rooms.
- Decision: 2026-11-12, user: Playwright for Python for integrated verification; CI is chosen once the code has a host, now in epic-deployment.
- Decision: 2026-11-12, user: validation wording, a capacity ceiling and picker search behavior are left to the stories; no spike needed. Story 2 set the ceiling at 200 and names at 50 characters; R7 follows.
- Decision: 2026-11-12, user: two stories only, both on the user's computer, to keep the walkthrough short. Sofia's nine-story draft (deploy bundle, host stand-up, CI, refactor sweep, integrated verification on the deployed app, finer people and rooms stories) was declined for now.
- Decision: 2026-11-12: tracer bullet is story 1, "Pick and switch your name, end to end": scaffold, people table, seed load and reload, picker, current person and shell, running locally.
- Decision: 2026-11-12: switching name and the seed reload are merged into story 1, and add, edit, close and reopen into story 2; if story 2 runs past one build session, split it into adding rooms and editing, closing and reopening them.
- Decision: 2026-11-12: no refactor sweep or closing end-to-end story, since the epic has two entries.
- Decision: 2026-11-12, user: deployment (deploy bundle and host stand-up), CI, integrated verification on the deployed app, loading HR's list and office managers' check on the live app move to a new epic, epic-deployment; this epic's Done when is cut to the user's computer and it closes. Supersedes the earlier decision that it stays open until they are planned here. The Rollout constraint and the open questions on hosting (OQ-4), the code host and HR's columns moved with them.
- Decision: 2026-11-12, user: closed as done. The closure check found Done when, R1 to R9 and the constraints met on the user's computer (`uv run pytest`: 80 passed, e2e at 1280 and 390 widths), and the user walked both stories at laptop and phone widths.
- Known issue, not ticketed: story 2 review finding 3, rejected there as unlikely: adding a room while another row is open for Edit or close confirmation discards that row and its typed values (`rooms/web.py` `add_room`). Raise it as a bug if office managers hit it.
