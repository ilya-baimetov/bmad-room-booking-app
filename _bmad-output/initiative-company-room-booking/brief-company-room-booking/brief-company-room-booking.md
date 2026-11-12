---
title: "Company Room Booking"
template: brief
version: 1.1.0
status: final
created: "2026-11-12"
updated: "2026-11-12"
---

# Company Room Booking

## Table of Contents

- [Executive summary](#executive-summary): what it is, who it is for, why now
- [Problem](#problem): room hunting, double bookings, no-shows, per-office spreadsheets
- [Solution](#solution): one standalone booking tool across three offices
- [What makes it different](#what-makes-it-different): versus spreadsheets, calendar room booking, bought products
- [Who it serves](#who-it-serves): all staff, office managers
- [Success criteria](#success-criteria): zero double bookings, free room in seconds, spreadsheets retired
- [Scope](#scope): first release in and out, check-in deferred
- [Open questions](#open-questions): recurring bookings, spreadsheet cutover
- [Assumptions](#assumptions): unconfirmed inferences, by section

## Executive summary

Company Room Booking is one place where everyone in the company can find a free meeting room and book it, across all three offices. Today each office keeps its own shared spreadsheet, and people also name rooms in calendar invites, so nobody has a single true picture of which rooms are taken. People waste time hunting for rooms, and rooms get double-booked.

This matters now because the company has grown to three offices and more people are back in the office, so room hunting got worse this year. The first release serves about 300 staff and the office managers who look after the rooms. It does two things well: it makes double bookings impossible, and it lets anyone find a free room in seconds.

Rooms that are booked but sit empty because nobody turns up are a known problem that the first release does not solve. Checking in at the room to free those rooms comes next.

## Problem

People waste time hunting for rooms, rooms get double-booked, and booked rooms often sit empty because nobody turns up.

Today each of the three offices keeps its own shared spreadsheet of room bookings, and people also name rooms in calendar invites. Room booking is not set up in the company calendar. With two places to record a booking and no single source of truth, different people can claim the same room, one in an invite and another in the spreadsheet. Someone looking for a room has to open the right office's spreadsheet and still can't trust it.

It got worse this year: the company grew to three offices, and more people are back in the office.

## Solution

A standalone room-booking tool that holds every bookable room in all three offices and is the only place bookings are made.

- **Finding a room:** a staff member picks an office and a time and sees which rooms are free, in seconds. This answers the hunting.
- **Booking a room:** the tool refuses a booking that clashes with an existing one, so a room can't be double-booked. This answers the double bookings.
- **Looking after rooms:** office managers keep their office's room list current. This keeps the room list accurate.

## What makes it different

The alternatives are the current spreadsheets, turning on room booking in the company calendar, or buying a room-booking product.

- **Versus the spreadsheets:** one place for all three offices instead of three files and invites, and clashes are blocked when a booking is made rather than found afterwards.
- **Versus calendar room booking or a bought product:** the reason to stay standalone is still an assumption (A6).

The real advantage is focus: it does the two things the offices are struggling with, and nothing else.

## Who it serves

- **Staff (about 300, across three offices):** anyone who needs a room for a meeting. Success for them is finding and booking a free room in seconds and trusting it will be theirs when they arrive.
- **Office managers:** the people who look after each office's rooms. Success for them is an accurate room list and no clashes to settle.

## Success criteria

- **No double bookings:** zero clashes after launch, enforced by the tool.
- **A free room in seconds:** under 10 seconds from opening the tool to seeing a free room for a given office and time (unconfirmed, A9).
- **Adoption:** the per-office spreadsheets are retired in all three offices within four weeks of launch (unconfirmed, A10).
- **Stop signal:** if, six weeks after launch, people are still booking in spreadsheets or only in invites, stop and find out why before building more (unconfirmed, A11).

## Scope

**In the first release:**

- All bookable rooms in all three offices, live together.
- Finding free rooms by office and time.
- Booking, changing and cancelling a booking, with clashes refused.
- Office managers managing their office's rooms.

**Out of the first release:**

- Checking in at the room to free rooms nobody turns up for. No-shows remain a known problem until then, and they are the next thing to solve.
- Connecting to the company calendar (unconfirmed, A5).
- Desk booking, displays outside rooms, and usage reports (unconfirmed, A12).

## Open questions

- **Recurring bookings:** do weekly team meetings need repeating bookings in the first release? Owner: John, in the PRD. Revisit when the PRD sets out booking rules.
- **Spreadsheet cutover:** at launch, are future bookings already in the spreadsheets moved into the tool, re-entered by their owners, or dropped? Owner: John, in the PRD. Revisit when the PRD plans the rollout.

## Assumptions

Proposed by Mary and given a blanket yes. None has been confirmed item by item, so each stays open until it is.

- **A1 · Problem:** the mismatch between invites and spreadsheets is the main cause of double bookings.
- **A2 · Problem:** office managers spend time settling clashes and keeping the spreadsheets tidy.
- **A3 · Solution:** it is a web tool that works in the browser on laptop and phone.
- **A4 · Solution:** office managers add and edit rooms and take a room out of use, for example during repairs.
- **A5 · Solution:** "standalone" means the first release does not connect to the company calendar; a booking lives in the tool, and people can still mention the room in their invite.
- **A6 · What makes it different:** a standalone tool keeps it simple and in the company's own hands, without reconfiguring the calendar system or paying per seat for features it does not need.
- **A7 · Who it serves:** staff include people booking a room in another office when visiting it.
- **A8 · Who it serves:** each office has one or more office managers.
- **A9 · Success criteria:** the 10-second threshold for finding a free room.
- **A10 · Success criteria:** the four-week deadline for retiring the spreadsheets.
- **A11 · Success criteria:** the six-week stop signal.
- **A12 · Scope:** desk booking, displays outside rooms, and usage reports are out of the first release.
