---
tracker_id: ""
type: epic
title: "Check in at the door or lose the room"
parent: initiative-check-in
covers: [R1, R2, R3, R4, R5, R6, R7, R8]
sources: [_bmad-output/initiative-check-in/initiative-check-in.md, _bmad-output/initiative-check-in/architecture-check-in/architecture-check-in.md]
companions: [_bmad-output/initiative-check-in/ux-door-screen/DESIGN.md, _bmad-output/initiative-check-in/ux-door-screen/EXPERIENCE.md, _bmad-output/initiative-check-in/architecture-check-in/architecture-check-in.md]
after: []
refined: true
risk: high
---

# Check in at the door or lose the room

## Description

The whole check-in initiative in one epic. Office managers set up, replace and remove a door tablet per room. The tablet shows the room's bookings for today and checks one in with one tap in its window. A booking nobody checks into is freed 15 minutes after its start, and the rest of its slot becomes bookable. Freed bookings show as freed to organisers and attendees, in the app and in their calendars. Office managers see this week's freed count. The initiative's Requirements, the door-screen UX and the architecture spine (AD-1–AD-12) settle most of it. Tablets and check-in may reach production before freeing does.

## Outcome

In rooms with a door tablet, bookings nobody turns up to go back to people who need them, and office managers see how many (the initiative's Outcome signal).

## Requirements

- R1 (parent R1): An office manager sets up a tablet once for one room in their office, and can remove it; a room has at most one tablet, so setting up a new one replaces the old. From setup until removal the tablet shows that room's page with no further sign-in.
- R2 (parent R2): The room's tablet page shows that room's bookings for today (UK day), and which one is current or next.
- R3 (parent R3): Anyone at the tablet checks in a booking with one tap, without saying who they are, from 5 minutes before its start until 15 minutes after; outside that window the tablet offers no check-in for it.
- R4 (parent R4): A booking with no check-in by 15 minutes after its start is freed: the rest of its slot, from 15 minutes after its start to its end, can be booked by anyone like any free time.
- R5 (parent R5): A freed booking shows as "Freed: nobody checked in" on My bookings and its details page, to its organiser and its attendees alike, and as cancelled in their subscribed calendars; it is distinct from a booking that was cancelled or simply ended. A freed booking cannot be cancelled; Book again still works.
- R6 (parent R6): An office manager sees, beside their office's rooms on Manage rooms, how many bookings in their office were freed from Monday to today, UK time.
- R7 (parent R7): A booking is freed only if its check-in window, from 5 minutes before its start to 15 minutes after, opens after freeing went live and its room had a tablet set up for the whole of that window; any other booking is never freed.
- R8 (parent R8; UX Component Patterns): A booking today in a room with a tablet shows, to its organiser and attendees on My bookings and its details page, its check-in window ("Check in at the door, 09:55–10:15") until checked in, freed or the window closes, and "Checked in" once checked in; bookings in rooms with no tablet show what they show today.
- R9 (parent R1; AD-8): On the tablet's own browser, an office manager signed in by Pick your name chooses "Set up door tablet" on a room's row in Manage rooms and confirms in the row, as for Close; the confirm row names the room and gives the mounting guidance (screen centre about 120 cm from the floor, tablet set never to sleep). Setup clears that browser's person cookie and lands on the door page.
- R10 (parent R1; AD-8): Each room's row on Manage rooms says whether it has a door tablet and since when; an office manager of that office removes it there, from any device, after a confirm in the row; the removed tablet then shows the not-set-up page.
- R11 (parent R6): The freed count is one line above the rooms table on Manage rooms, "Bookings freed since Monday: {n}", shown with 0 too.
- R12 (parent R5; architecture Deferred): A freed booking stays in the Rooms page's "Your upcoming bookings" until it ends, grey and tagged "Freed: nobody checked in" as on My bookings.
- R13 (parent R7): When freeing went live is the setting `ROOMBOOKER_FREEING_STARTS_AT` (UTC), read through `core.settings.get_settings()`; while it is unset nothing is freed and no screen says a booking will be freed (no door countdown, no "or the room is freed"), so tablets and check-in can ship first and the setting doubles as an off switch.

## Constraints

- C1–C6 (parent C1–C6) bind as written in the initiative: no QR codes, sensors, badges or notifications; plain web-page tablets; `bookings.service`'s lock and the overlap triggers stay the double-booking guarantee; time from `utc_now()` with the start + 15 boundary testable; every page a full page load; feed UIDs stable.

## Done when

- An office manager sets up a room's tablet (a browser window), and it shows today's bookings and checks one in only within its window; organisers and attendees see the window and "Checked in".
- A covered booking with no check-in is freed at start + 15 minutes, the rest of its slot is bookable, and it shows as "Freed: nobody checked in" on My bookings and details, as cancelled in subscribed calendars, with no Cancel.
- A checked-in booking, a booking whose window no tablet covered in full, and one whose window opened before freeing went live are never freed.
- An office manager sees this week's freed count for their office on Manage rooms.
- Runs on the user's computer with `ROOMBOOKER_FREEING_STARTS_AT` set, a browser window serving as a room's tablet.
- The tracer path from the initiative's Boundaries passes end to end in the e2e suite against the local app, with boundary tests at start − 5, start + 15 − 1 min and start + 15 (patched `core.time.utc_now`).

## Boundaries

- Everything in the initiative's Boundaries applies; this epic owns every touch point listed there.
- Out: booking from the tablet, and any link from the door page into the app.
- Must not change: rooms with no tablet, and every booking while `ROOMBOOKER_FREEING_STARTS_AT` is unset, behave exactly as today apart from check-in.

## References

- parent — _bmad-output/initiative-check-in/initiative-check-in.md, sections Requirements, Constraints, Boundaries, Notes
- architecture — _bmad-output/initiative-check-in/architecture-check-in/architecture-check-in.md, AD-1–AD-12, Consistency Conventions, Deferred
- design — _bmad-output/initiative-check-in/ux-door-screen/EXPERIENCE.md
- design — _bmad-output/initiative-check-in/ux-door-screen/DESIGN.md

## Notes

- Decision: (2026-11-13) An office manager may set up a tablet for any room in their office from that tablet's browser; the confirm row naming the room is the safeguard (user confirmed).
- Decision: (2026-11-13) Refined with Sofia's picks (the user's call): setup on Manage rooms from the tablet's browser with an in-row confirm, removal from any device (R9, R10); the count as one line above the rooms table (R11); a freed booking stays in Your upcoming bookings until it ends (R12); freeing go-live is the `FREEING_STARTS_AT` setting, unset meaning off (R13).
- Decision: (2026-11-13) Buying, mounting and powering the tablets is an operational step each office manager owns, outside this epic's stories; the epic supplies setup guidance (mounting height, never-sleep) with R9 (user confirmed).
- Decision: (2026-11-13) One epic for now (the user's call); Sofia's three-epic split (tablets and check-in, freeing, weekly count) is the fallback if stories run past twelve.
- Decision: (2026-11-13) As few stories as possible, each one build session (the user's call): five stories; Sofia's twelve-story draft merged.
- Decision: (2026-11-13) Everything runs on the user's computer, the tablet being a browser window (the user's call): no real-tablet person steps, no production release or office rollout in this epic.
- Decision: (2026-11-13) Refactor sweep declined under "as few as you can"; cleanup stays inside each build's own review.
- Decision: (2026-11-13) The e2e server moves time through a clock offset in core.time, set by the e2e harness through a non-production setting and refused when ROOMBOOKER_ENV is production; story 5 builds it (Sofia's pick, the user's call).
- Decision: (2026-11-13) Five stories approved in build order 1 → 2 → 3 → 4 → 5.
- Decision: (2026-11-13) Tracer bullet is story 1, tablet setup through check-in at /door; story 2, freeing and rebooking, follows as the least certain part.
