---
tracker_id: ""
type: initiative
title: "Room bookings show up in the calendar app people already use"
parent: none
sources: [_bmad-output/initiative-calendar-export/sources/request-2026-11-13.md]
companions: []
after: []
risk: medium
---

# Room bookings show up in the calendar app people already use

## Description

People in the London, Manchester and Leeds offices keep their days in Outlook, Google Calendar or Apple Calendar, but their room bookings live only in the room booker. When this initiative is done, any booking can be added to a calendar as a one-off file. Each person also has a private feed address their calendar app subscribes to, and it keeps their bookings current as they change or are cancelled. The room booker stays the only place to book. The request is in `sources/request-2026-11-13.md`.

## Outcome

Staff see the rooms they organise or attend in their own calendar app without retyping them. The signal: a subscribed calendar shows a new, changed or cancelled booking correctly after its next refresh, in all three apps.

## Requirements

- R1 (S1, S2): From a booking, a person downloads an Add to calendar .ics file; opened in Outlook, Google Calendar or Apple Calendar it adds that booking as one event at its correct UK time.
- R2 (S1, S3): Each person has their own private feed address; subscribed in Outlook, Google Calendar or Apple Calendar it shows every booking they organise or attend, at the correct UK time.
- R3 (S3): After a booking is changed, the subscribed calendar shows the change on its next refresh; after a booking is cancelled, including by its room closing, it is gone on the next refresh.
- R4 (S4): A feed address cannot be guessed or worked out from the person's name, email or id; a request without a valid address gets no bookings.
- R5 (S4): A person resets their feed address; afterwards the old address returns no bookings and the new one shows them.
- R6 (S3, S4): A person can see and copy their own feed address in the room booker, and only their own.

## Constraints

- C1 (S5): No sign-in to Microsoft or Google and no calls to their calendar APIs; the export is files and a feed address only.
- C2 (S5): One way only: nothing is read back from any calendar app; the room booker stays the only place to book, change or cancel.
- C3 (S1, S2): Standard iCalendar that Outlook, Google Calendar and Apple Calendar all accept as-is; no per-app formats.
- C4 (S3): The feed is fetched by calendar apps that send no cookie and do not follow a redirect to Pick your name, so it cannot rely on the current-person cookie.

## Done when

- An Add to calendar download opens as the right single event, at the right time, in Outlook, Google Calendar and Apple Calendar.
- A feed subscribed in each of the three apps shows the person's organised and attended bookings, and a booking edit, a cancellation and a room closure each show up after the app refreshes.
- Resetting a feed address stops the old address returning bookings and the new address works.
- Events land at the correct UK time on both sides of a clock change (GMT and BST).
- Both features are live in production for all three offices.

## Boundaries

- Out: signing in to Microsoft or Google, syncing anything back, and booking, changing or cancelling from a calendar app.
- Out: a downloaded file updating itself; the feed is how a calendar stays current.
- Touch point: bookings — reads the bookings a person organises or attends; not yet sliced, no epic.
- Touch point: people — each person's feed secret and its reset (a new migration); not yet sliced, no epic.
- Touch point: calendar — My bookings shows the feed address; the booking details page offers Add to calendar; not yet sliced, no epic.
- Must not change: how bookings are made, the overlap rules, or what My bookings lists today.
- Tracer path: a person copies their feed address from My bookings, subscribes in their calendar app, books a room, and sees it appear after the app refreshes.

## References

- source — _bmad-output/initiative-calendar-export/sources/request-2026-11-13.md, S1–S5
- code — roombooker/core/identity.py (identity is only the Pick your name cookie)
- code — roombooker/calendar/service.py, my_bookings (organised or attended)
- decision — docs/decisions/adr-closing-a-room-deletes-its-future-bookings.md

## Notes

- Decision: (2026-11-13) The feed covers bookings from 30 days ago onward, with no upper limit.
- Decision: (2026-11-13) Each event shows the booking title, start and end, the room and office as location, and the organiser.
- Decision: (2026-11-13) A cancelled booking simply disappears from the feed; no cancelled events are kept or shown.
- Decision: (2026-11-13) How soon changes appear is set by each calendar app's refresh interval (Google Calendar can take hours); the room booker cannot push updates.
- Decision: (2026-11-13) The feed address and its reset live on My bookings; Add to calendar sits on a booking's details page.
- Decision: (2026-11-13) A downloaded .ics file is a snapshot and does not change when the booking later changes; the feed is the way to stay current.
- Decision: (2026-11-13) When a person is made inactive their feed address stops returning bookings.
- Decision: (2026-11-13) Room-wide or office-wide calendars (for office managers or room displays) are out of this initiative.
