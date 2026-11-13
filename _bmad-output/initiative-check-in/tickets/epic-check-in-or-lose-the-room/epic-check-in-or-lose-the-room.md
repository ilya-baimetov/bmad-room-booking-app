---
tracker_id: ""
type: epic
title: "Check in at the door or lose the room"
parent: initiative-check-in
covers: [R1, R2, R3, R4, R5, R6, R7, R8]
sources: []
companions: [_bmad-output/initiative-check-in/ux-door-screen/DESIGN.md, _bmad-output/initiative-check-in/ux-door-screen/EXPERIENCE.md, _bmad-output/initiative-check-in/architecture-check-in/architecture-check-in.md]
after: []
refined: false
risk: high
---

# Check in at the door or lose the room

## Description

The whole check-in initiative in one epic. Office managers set up, replace and remove a door tablet per room. The tablet shows the room's bookings for today and checks one in with one tap in its window. A booking nobody checks into is freed 15 minutes after its start, and the rest of its slot becomes bookable. Freed bookings show as freed to organisers and attendees, in the app and in their calendars. Office managers see this week's freed count. The initiative's Requirements, the door-screen UX and the architecture spine (AD-1–AD-12) settle most of it. Tablets and check-in may reach production before freeing does.

## Outcome

In rooms with a door tablet, bookings nobody turns up to go back to people who need them, and office managers see how many (the initiative's Outcome signal).

## Done when

- In production, an office manager sets up a room's tablet, and it shows today's bookings and checks one in only within its window; organisers and attendees see the window and "Checked in".
- In production, a covered booking with no check-in is freed at start + 15 minutes, the rest of its slot is bookable, and it shows as "Freed: nobody checked in" on My bookings and details, as cancelled in subscribed calendars, with no Cancel.
- A checked-in booking, a booking whose window no tablet covered in full, and one whose window opened before freeing went live are never freed.
- An office manager sees this week's freed count for their office on Manage rooms.
- Live in production for all three offices, with tablets set up in the rooms that have one.
- The tracer path from the initiative's Boundaries passes end to end against the deployed app, with boundary tests at start − 5, start + 15 − 1 min and start + 15 (patched `core.time.utc_now`).

## Boundaries

- Everything in the initiative's Boundaries applies; this epic owns every touch point listed there.
- Open for refinement: tablet setup and removal flow and wording (R1); the freed count's placement and wording on Manage rooms (R6); whether a freed booking stays in the Rooms page's "Your upcoming bookings"; where the "freeing went live" moment is recorded (R7).

## References

- parent — _bmad-output/initiative-check-in/initiative-check-in.md, sections Requirements, Constraints, Boundaries, Notes
- architecture — _bmad-output/initiative-check-in/architecture-check-in/architecture-check-in.md, AD-1–AD-12, Consistency Conventions, Deferred
- design — _bmad-output/initiative-check-in/ux-door-screen/EXPERIENCE.md
- design — _bmad-output/initiative-check-in/ux-door-screen/DESIGN.md

## Notes

- Assumption: Buying, mounting and powering the tablets is an operational step each office manager owns, outside this epic's stories; the epic supplies setup guidance (mounting height, kiosk or never-sleep) with R1.
- Decision: (2026-11-13) One epic for now (the user's call); Sofia's three-epic split (tablets and check-in, freeing, weekly count) is the fallback if stories run past twelve.
