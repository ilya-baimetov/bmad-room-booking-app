---
type: epic
title: Office managers keep their rooms current
parent: initiative-company-room-booking
covers: [R1, R2, R3, R4, R5]
sources: []
companions: []
after: []
refined: false
risk: medium
---

# Office managers keep their rooms current

## Description

The deployed app's first release: anyone picks their name from the seeded people, and an office manager adds, edits, closes and reopens their own office's rooms. It lays the ground the later epics build on: the scaffold, the database, seed loading, deployment, the app shell, the type-ahead people picker, the current person and the office-manager check. Office managers can enter and check their rooms on the live app before go-live, as the initiative's rollout asks.

## Outcome

Office managers in London, Manchester and Leeds keep an accurate room list on the deployed app, so the rooms exist before anyone books (initiative R1 to R5).

## Done when

- On the deployed app, a person picks their name from the seeded people, the app shows it throughout, and the device remembers it until they switch.
- An office manager adds, edits, closes and reopens rooms in their own office only; anyone else is refused.
- A closed room shows as Closed.
- Offices, people, home offices and office-manager marks load from the seed file, and the same load accepts HR's list.
- Integrated verification on the deployed app passes, on laptop and phone.

## Boundaries

- Not here: finding free rooms, bookings, refusing bookings of a closed room, the future-booking count when closing, or what happens to those bookings; all epic-find-and-book.
- Not here: the calendar; epic-my-calendar.
- Not here: editing people or offices inside the app (initiative Boundaries).
- Owns for later epics: the shell (top bar with the current name, tabs, DESIGN.md tokens), the people picker, the current person and the office-manager check.

## References

- parent — _bmad-output/initiative-company-room-booking/initiative-company-room-booking.md, section Requirements (R1 to R5) and Constraints
- experience — _bmad-output/initiative-company-room-booking/ux-company-room-booking/EXPERIENCE.md, Pick your name, Manage rooms, Rooms table
- design — _bmad-output/initiative-company-room-booking/ux-company-room-booking/DESIGN.md
- architecture — _bmad-output/initiative-company-room-booking/architecture-company-room-booking/architecture-company-room-booking.md, AD-1, AD-2, AD-3, AD-6, AD-7, AD-9, AD-10, AD-11, AD-12, Structural Seed

## Notes

- Unknown: hosting and the shared technical decisions are unsettled until the bmad-architecture spine exists; the baseline stories wait on it.
- Decision: 2026-11-12, user: opening epic, because nothing can be booked until rooms exist; the platform baseline is its first stories.
