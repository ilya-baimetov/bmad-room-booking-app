---
tracker_id: ""
type: initiative
title: "Booked rooms nobody turns up to are freed for others"
parent: none
sources: [_bmad-output/initiative-check-in/sources/request-2026-11-13.md, _bmad-output/research-booking-lifecycle-and-end/research-booking-lifecycle-and-end.md]
companions: []
after: []
risk: high
---

# Booked rooms nobody turns up to are freed for others

## Description

Booked rooms in the London, Manchester and Leeds offices often sit empty because nobody turns up. When this initiative is done, each room with a tablet by its door shows that room's bookings for today. People check in there from 5 minutes before a booking starts until 15 minutes after. A booking nobody checks into by then is freed: the rest of its slot becomes bookable by anyone, and its organiser sees it as freed. Office managers see how many bookings their office freed this week. It changes how bookings end in the existing room booker, which today deletes a booking to stop it blocking its slot. The request and the answers that shaped it are in `sources/request-2026-11-13.md`. How bookings end today is in the booking-lifecycle research.

## Outcome

Rooms that were booked and then abandoned go back to people who need them. The signal: in a room with a tablet set up, an unclaimed booking is freed 15 minutes after its start, someone else can book the rest of the slot, and the office manager's weekly count goes up by one (S15: no numeric target this release).

## Requirements

- R1 (S4, S9): An office manager sets up a tablet once for one room in their office; from then on the tablet shows that room's page with no further sign-in.
- R2 (S4): The room's tablet page shows that room's bookings for today (UK day), and which one is current or next.
- R3 (S5, S11): Anyone at the tablet checks in a booking with one tap, without saying who they are, from 5 minutes before its start until 15 minutes after; outside that window the tablet offers no check-in for it.
- R4 (S3, S6): A booking with no check-in by 15 minutes after its start is freed: the rest of its slot, from 15 minutes after its start to its end, can be booked by anyone like any free time.
- R5 (S6, S12): A freed booking shows as "Freed: nobody checked in" on its organiser's My bookings and on its details page, and as cancelled in their subscribed calendar; it is distinct from a booking that was cancelled or simply ended.
- R6 (S7, S14): An office manager sees, beside their office's rooms on Manage rooms, how many bookings in their office were freed from Monday to today, UK time.
- R7 (S13): A booking in a room whose tablet has not been set up is never freed.

## Constraints

- C1 (S8): No QR codes, sensors, badges or notifications in this release.
- C2 (S9): The tablets are ordinary tablets showing a web page of the app; no native app or device management.
- C3 (S10; research §1, §3): Today a booking stops blocking its slot only when its row is deleted, since the overlap guard counts every row, and nothing records how a booking ended. Freeing must keep `bookings.service`'s write lock and the overlap triggers as the double-booking guarantee (AGENTS.md).
- C4 (S10; research §1, §5): Python reads time from `core.time.utc_now()` while SQLite triggers read their own clock, and tests cannot fake it. Release must be testable at its boundary, 15 minutes after the start exactly.
- C5 (AGENTS.md): Every page, the tablet's included, works as a full page load; htmx only narrows the swap.
- C6 (S12; research §2): Subscribed calendar feeds today drop cancelled bookings and key events by a UID hashing room, start, end and title. Showing a booking as freed there must not re-create or break other events in existing subscriptions.

## Done when

- A tablet set up by an office manager shows its room's bookings for today and checks one in within the window, and only within it.
- A booking nobody checks into is freed 15 minutes after its start, and someone else can then book the rest of its slot; a checked-in booking, or one in a room with no tablet set up, is never freed.
- The organiser sees a freed booking as freed on My bookings, its details page and their subscribed calendar.
- An office manager sees this week's freed count for their office on Manage rooms.
- Live in production for all three offices.

## Boundaries

- Out: QR codes, sensors, badges, notifications of any kind (C1).
- Out: booking a room from the tablet; the tablet only shows today's bookings and checks them in.
- Out: knowing who checked in; check-in is anonymous (S11).
- Out: a numeric target for freed bookings this release (S15).
- Touch point: rooms — which rooms have a tablet set up, and the freed count on Manage rooms.
- Touch point: bookings — check-in, freeing, and what freed means for overlap and listings.
- Touch point: calendar — My bookings and the subscribed feed show freed bookings.
- Must not change: how a booking is made, cancelled, or removed by closing its room; the overlap guarantee; rooms with no tablet behave exactly as today.
- Tracer path: an office manager sets up a room's tablet; a booking in that room passes 15 minutes after its start with no check-in; it is freed; someone else books the rest of the slot; the organiser sees it as freed; the manager's weekly count shows it.

## References

- source — _bmad-output/initiative-check-in/sources/request-2026-11-13.md, S1–S15
- research — _bmad-output/research-booking-lifecycle-and-end/research-booking-lifecycle-and-end.md, §1 (how bookings end), §2 (what reads end time), §3 (triggers), §5 (time in tests)
- decision — docs/decisions/adr-closing-a-room-deletes-its-future-bookings.md
- code — roombooker/core/identity.py (identity is only the Pick your name cookie)

## Notes

- Assumption: Anyone can check in a booking they are not part of, so a passer-by can keep a booking from being freed; accepted for this release (S11).
- Decision: (2026-11-13) Requirements written with Sofia directly, no PRD (the user's call).
- Decision: (2026-11-13) No numeric success target this release (S15).
