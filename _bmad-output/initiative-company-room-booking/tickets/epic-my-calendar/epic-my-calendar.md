---
type: epic
title: Each person sees their own bookings by day and week
parent: initiative-company-room-booking
covers: [R7, R12, R13, R14]
sources: []
companions: []
after: []
refined: false
risk: low
---

# Each person sees their own bookings by day and week

## Description

A person sees every booking they organise or attend in a built-in calendar, by day and by week, moves between days and weeks, and opens a booking to change or cancel it. It reuses epic-offices-and-rooms' shell and epic-find-and-book's date switcher and booking details panel, so it adds the calendar views, not new booking rules.

## Outcome

Each person trusts the app as their only room calendar, which retires the spreadsheets (initiative SM-3).

## Done when

- On the deployed app, a person's day and week views show every booking they organise and every one they attend, including bookings others added them to.
- A person moves to the previous or next day or week.
- Opening a booking from the calendar allows change or cancel only under RULE-3, and the calendar updates at once.
- Integrated verification on the deployed app passes, on laptop and phone.

## Boundaries

- Not here: making, changing or cancelling bookings and their rules; epic-find-and-book, reused through its booking details panel.
- R7 here is its calendar side only: a booking showing in the organiser's and every attendee's calendar.
- Not here: outside calendars or notifications (initiative Boundaries).

## References

- parent — _bmad-output/initiative-company-room-booking/initiative-company-room-booking.md, section Requirements (R7, R12 to R14) and Constraints
- experience — _bmad-output/initiative-company-room-booking/ux-company-room-booking/EXPERIENCE.md, My bookings, My bookings calendar, Responsive & Platform
- design — _bmad-output/initiative-company-room-booking/ux-company-room-booking/DESIGN.md
- architecture — _bmad-output/initiative-company-room-booking/architecture-company-room-booking/architecture-company-room-booking.md, AD-3, AD-5, AD-7, AD-8, AD-13

## Notes

- Waits on epic-find-and-book because: it needs bookings with attendees, the date switcher, and the booking details panel with Change and Cancel.
