---
type: epic
title: Anyone finds a free room and books it, with no double bookings
parent: initiative-company-room-booking
covers: [R5, R6, R7, R8, R9, R10, R11, R15, R16]
sources: []
companions: []
after: []
refined: false
risk: high
---

# Anyone finds a free room and books it, with no double bookings

## Description

The heart of the initiative: on laptop and phone, a person sees which rooms in any office are free for any date, time and length, books one with attendees in three taps or fewer, and the organiser or an office manager changes or cancels it. Overlapping bookings and bookings of closed rooms are refused, and closing a room shows and settles its future bookings. It reuses epic-offices-and-rooms' shell, people picker and office-manager check, and owns the bookings data, the date switcher and the booking details panel that epic-my-calendar reuses.

## Outcome

Staff in all three offices find and book a free room in seconds with no double bookings, the change behind initiative SM-1 and SM-2.

## Done when

- On the deployed app, a person sees free rooms for any office, date, start time and length on laptop and phone, within 10 seconds of opening the app.
- A booking of a free room takes three taps or fewer; an overlapping booking or change, or a booking of a closed room, is refused with the reason, even when two people book at once.
- The organiser and the room's office managers change and cancel bookings; nobody else can, and a cancelled room is free to everyone at once.
- Attendees are visible only to the organiser, the attendees and the room's office managers.
- Integrated verification on the deployed app passes.

## Boundaries

- Not here: rooms, the current person and the shell; epic-offices-and-rooms.
- Not here: showing bookings in a person's calendar; epic-my-calendar (initiative R7 is shared).
- R5 here is its booking side only: refusing bookings of a closed room, the future-booking count on the close confirmation, and what happens to those bookings.
- Replaces epic-offices-and-rooms' "Booking opens soon." landing with Rooms and adds its tab (epic-offices-and-rooms R9).
- Owns for epic-my-calendar: the bookings data, the date switcher and the booking details panel with Change and Cancel.

## References

- parent — _bmad-output/initiative-company-room-booking/initiative-company-room-booking.md, section Requirements (R5 to R11, R15, R16) and Constraints
- experience — _bmad-output/initiative-company-room-booking/ux-company-room-booking/EXPERIENCE.md, Rooms, Booking sheet, Booking details, Booking Visibility, State Patterns
- design — _bmad-output/initiative-company-room-booking/ux-company-room-booking/DESIGN.md
- architecture — _bmad-output/initiative-company-room-booking/architecture-company-room-booking/architecture-company-room-booking.md, AD-3, AD-4, AD-5, AD-7, AD-8, AD-12, AD-13

## Notes

- Open question: What happens to a closed room's future bookings (PRD FR-5); settled when this epic is refined.
- Source conflict: R6 — the initiative (user decision 2026-11-12: phone Rooms keeps "free now" as default and adds a "Later" date, time and length choice) vs EXPERIENCE.md's phone list, which starts from the next quarter-hour with 30 min, 1 h or 2 h only. R6 wins; bmad-ux can update EXPERIENCE.md at refinement.
- Waits on epic-offices-and-rooms because: it needs the app with offices, people, rooms, closed-room status, the shell, the people picker, the current person and the office-manager check.
- Waits on epic-deployment because: its integrated verification runs on the deployed app; only the entry for that check waits on it, so the other stories can be built first.
- Decision: 2026-11-12, user: deployment moved from epic-offices-and-rooms to epic-deployment; this epic builds on the local app and waits on epic-deployment only for its check on the deployed app.
- Decision: 2026-11-12, user: owns the fate of a closed room's future bookings, moved from the rooms epic because bookings exist only here.
