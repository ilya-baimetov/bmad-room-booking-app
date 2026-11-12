---
type: initiative
title: Company Room Booking
parent: none
sources:
  - _bmad-output/initiative-company-room-booking/prd-company-room-booking/prd-company-room-booking.md
  - _bmad-output/initiative-company-room-booking/brief-company-room-booking/brief-company-room-booking.md
  - _bmad-output/initiative-company-room-booking/ux-company-room-booking/EXPERIENCE.md
companions:
  - _bmad-output/initiative-company-room-booking/ux-company-room-booking/EXPERIENCE.md
  - _bmad-output/initiative-company-room-booking/ux-company-room-booking/DESIGN.md
  - _bmad-output/initiative-company-room-booking/architecture-company-room-booking/architecture-company-room-booking.md
after: []
risk: high
---

# Company Room Booking

## Description

One web app where anyone in the company finds a free meeting room in London, Manchester or Leeds and books it, with double bookings made impossible. It replaces the three per-office spreadsheets and rooms named in calendar invites, which grew unworkable this year as the company reached three offices and more people came back in. Release one has no accounts and no outside calendars: people pick their name, book, and see their bookings in a built-in calendar; office managers keep their office's rooms current. Inputs: the final brief, PRD and UX (References).

## Outcome

About 300 staff and their office managers find and book rooms in one trusted place instead of three spreadsheets, shown by PRD SM-1 to SM-3 and watched by the SM-4 stop signal and the SM-5 counter-metric.

## Requirements

- R1 (FR-1): A person picks their name from the loaded people and then uses the app as that person, with their name shown throughout.
- R2 (FR-2): A person can switch to another name at any time; the picked name is remembered on that device until they switch.
- R3 (FR-3): An office manager adds a room to their office, with at least a name and a capacity.
- R4 (FR-4): An office manager edits a room in their office.
- R5 (FR-5, RULE-5): An office manager closes and reopens a room in their office; a closed room shows as closed and cannot be booked.
- R6 (FR-6): A person chooses an office, a date, a start time and a length and sees which of that office's rooms are free, on a laptop and on a phone, for any time, not only from now; their home office is shown first and any office can be chosen.
- R7 (FR-7, UJ-1): A person books a free room by giving a start time, a length from 15 minutes to 4 hours, a title and attendees from the loaded people; they become its organiser, and the booking shows in their calendar and every attendee's.
- R8 (FR-8): Any booking, or change to a booking, that would overlap another booking of the same room is refused, and the person is told why.
- R9 (FR-9): The organiser changes a booking's room, start time, length, title or attendees under the same rules as a new booking.
- R10 (FR-10): An office manager changes any booking of a room in their office under the same rules as R9.
- R11 (FR-11): The organiser, or an office manager of the room's office, cancels a booking, and the room shows as free to everyone at once.
- R12 (FR-12): A person sees their own bookings, both those they organise and those they attend, in a built-in calendar by day and by week.
- R13 (FR-13): From their calendar a person opens one of their bookings and changes or cancels it when RULE-3 allows.
- R14 (FR-14): A person moves their calendar to the previous or next day or week.
- R15 (EXPERIENCE Booking Visibility): Everyone sees a booking's room, time, title and organiser; its attendees are shown only to the organiser, the attendees and office managers of the room's office.
- R16 (EXPERIENCE Interaction Primitives): A person books a free room in three taps or fewer, with no typing required.

## Constraints

- RULE-1, PRD Decisions: Two bookings of the same room never overlap in time; there is no override, for office managers either.
- RULE-2: A booking lasts from 15 minutes to 4 hours; start times and lengths move in 15-minute steps.
- RULE-3: Only a booking's organiser and the office managers of the room's office may change or cancel it.
- RULE-4: Only office managers may add, edit, close or reopen rooms, and only in their own office, which is their home office.
- RULE-6: No accounts or passwords in release one; anyone can pick anyone's name, and every booking shows its organiser.
- RULE-7: Built with Python, FastAPI and SQLite; the user's computer is for building and testing, and where it runs for the company is decided in the architecture.
- RULE-8: Free rooms for a given office and time are visible in under 10 seconds from opening the app.
- RULE-9: Every feature works in a browser on a laptop and on a phone.
- PRD Quality and constraints: One time zone, UK time, for all three offices.
- PRD Decisions, Rollout: Before go-live office managers check their office's rooms are in the app and correct; at go-live the spreadsheets are frozen and organisers re-enter their own future bookings, so no spreadsheet import is built.
- User, 2026-11-12: Offices, people, home offices and office-manager marks load from a seed file while building; HR supplies the real list before go-live, and it loads the same way.

## Done when

- All five capabilities (picking your name, rooms, finding a free room, booking, my calendar) are live for London, Manchester and Leeds, reachable on laptop and phone where the company hosts the app.
- Zero overlapping bookings after go-live (SM-1).
- A person sees a free room for a given office and time in under 10 seconds from opening the app (SM-2).
- No office uses its spreadsheet for new bookings four weeks after go-live (SM-3).
- Office managers report no bookings made or changed under someone's name without them in the first six weeks, or sign-in is brought forward (SM-5).

## Boundaries

Release one only. Out, per PRD Non-goals and MVP scope:

- Check-in at the room and freeing no-show rooms (the next release).
- Visitors or bookings for people outside the company.
- Catering, equipment requests and room set-up.
- Desk booking, displays outside rooms and usage reports.
- Links to outside calendars: no Outlook, Google or other sync, invites or feeds.
- Notifications of any kind.
- Accounts, passwords or sign-in, including single sign-on.
- Loading or editing people or offices inside the app.
- Recurring bookings.
- Touch point: none. The app is standalone and connects to no calendar, directory or other system.
- Tracer path: a person picks their name, sees free rooms in their office, books one with attendees, finds it in their and the attendees' calendars, then changes or cancels it, while an office manager closes a room and it stops showing as free.

## References

- prd — _bmad-output/initiative-company-room-booking/prd-company-room-booking/prd-company-room-booking.md, Features and requirements (FR-1 to FR-14), Rules (RULE-1 to RULE-7), Quality and constraints (RULE-8, RULE-9), Success metrics, Non-goals, Decisions, Open questions, Assumptions
- brief — _bmad-output/initiative-company-room-booking/brief-company-room-booking/brief-company-room-booking.md, Problem, Success criteria
- experience — _bmad-output/initiative-company-room-booking/ux-company-room-booking/EXPERIENCE.md: surfaces, Booking Visibility, component and state patterns, key flows, accessibility floor
- design — _bmad-output/initiative-company-room-booking/ux-company-room-booking/DESIGN.md: visual identity and tokens
- architecture — _bmad-output/initiative-company-room-booking/architecture-company-room-booking/architecture-company-room-booking.md: AD-1 to AD-13 (paradigm, table ownership, overlap enforcement, UK time, current person, authorisation, hosting), Capability → Architecture Map, Deferred

## Notes

- Assumption: The picked name is remembered per device (R2, PRD A2).
- Assumption: A room has at least a name and a capacity (R3, PRD A3).
- Assumption: A person's calendar includes bookings they attend, not only those they organise (R12, PRD A4).
- Assumption: Start times and lengths move in 15-minute steps (RULE-2, PRD A5).
- Assumption: An office manager's own office is their home office (RULE-4, PRD A6).
- Assumption: No notifications, recurring bookings, displays or usage reports in release one (Boundaries, PRD A7, A9, A10).
- Assumption: People and offices are loaded and changed outside the app (Boundaries, PRD A8).
- Assumption: The success thresholds (10 seconds, four-week retirement, six-week stop signal, SM-5 trigger) are unconfirmed (PRD A11 to A14).
- Assumption: One UK time zone serves all three offices (PRD A15).
- Assumption: All three offices go live on one date (PRD A16).
- Open question: Go-live date (PRD OQ-1). Owner: user. Blocks rollout planning.
- Open question: How long past bookings are kept, and what data-protection duty applies to staff names and attendee lists (PRD OQ-3); also decides whether a cancelled booking stays deleted (architecture AD-13). Owner: user. Needed before go-live.
- Open question: Which host runs the app, and can it be reached only from company networks (office Wi-Fi, VPN) as architecture AD-11 assumes, since there is no sign-in (PRD OQ-4, narrowed by AD-11). Owner: user with IT. Blocks epic-offices-and-rooms' deployment story, not its other stories.
- Open question: What happens to a closed room's future bookings (PRD FR-5). Owner: epic-find-and-book.
- Decision: 2026-11-12, user: the first epic is offices and rooms, because nothing can be booked until rooms exist; the platform baseline is its first stories. Sofia's default would have opened on the booking path, the riskiest (RULE-1 under concurrent bookings); the user's order also lets office managers enter and check rooms on the live app before go-live, as the rollout asks.
- Decision: 2026-11-12, user: approved three epics in build order: offices and rooms, find and book, my calendar (tickets/tickets.toml).
- Decision: 2026-11-12, user: the fate of a closed room's future bookings moves from the rooms epic to epic-find-and-book, because bookings exist only there; epic 1's close only marks the room closed.
- Decision: 2026-11-12: shared decisions (hosting, rendering, data model, UK time, overlap enforcement under concurrent bookings, the remembered name, the office-manager check) go to a bmad-architecture spine before epic 1 is built.
