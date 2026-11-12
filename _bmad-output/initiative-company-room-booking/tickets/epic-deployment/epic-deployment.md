---
type: epic
title: The app is live on the company host
parent: initiative-company-room-booking
covers: []
sources: []
companions: []
after: []
refined: false
risk: medium
---

# The app is live on the company host

## Description

Puts the app built on the user's computer onto the company host, so office managers can check their rooms on the live app before go-live and every later epic deploys the same way. It takes over the deployment work epic-offices-and-rooms deferred: a deploy bundle (Dockerfile, Caddyfile, Litestream config) that runs locally first, standing it up on the host per architecture AD-11, CI once the code has a host, integrated verification on the deployed app, and loading HR's list there.

## Outcome

Office managers in London, Manchester and Leeds reach the live app from company networks on laptop and phone and confirm their office's rooms are correct before go-live (initiative Rollout constraint; Done when, "live ... where the company hosts the app").

## Done when

- The deploy bundle runs the app locally as it will run on the host, with Litestream backups.
- The app runs on the company host per AD-11, reachable from company networks on laptop and phone, and not from outside them if OQ-4 confirms that.
- CI runs the test suite on every change once the code has a host.
- HR's list loads onto the deployed app with the seed command, columns adapted, keeping everyone's id.
- Integrated verification (epic-offices-and-rooms' Playwright suite) passes on the deployed app at laptop and phone widths, and office managers confirm their rooms there.

## Boundaries

- Not here: features; picking a name and rooms are epic-offices-and-rooms', bookings epic-find-and-book's, the calendar epic-my-calendar's. Each later epic deploys its own work through this epic's path.
- Not here: sign-in or single sign-on (initiative Boundaries); network reach stands in for it per AD-11.
- Not here: spreadsheet import; organisers re-enter their own future bookings at go-live (initiative Rollout constraint).

## References

- parent — _bmad-output/initiative-company-room-booking/initiative-company-room-booking.md, section Constraints (RULE-6, RULE-7, RULE-9, Rollout, seed file) and Done when
- architecture — _bmad-output/initiative-company-room-booking/architecture-company-room-booking/architecture-company-room-booking.md, AD-9, AD-10 (`alembic upgrade head` as a deploy step), AD-11, Stack (Caddy and Litestream), Structural Seed (`deploy/`, Environments), Deferred
- source epic — _bmad-output/initiative-company-room-booking/tickets/epic-offices-and-rooms/epic-offices-and-rooms.md, Notes (deployment split, deferral, move)

## Notes

- Open question: Host provider and company-network-only reach (initiative OQ-4). Owner: user with IT. Blocks standing the app up on the host, not the deploy bundle.
- Open question: Where the code is hosted, which decides CI. Owner: user. Blocks CI only; `uv run pytest` is the check until then.
- Open question: HR's column names. Owner: user with HR. Needed before HR's list loads; the seed columns adapt, the email key holds.
- Open question: Go-live date (initiative OQ-1). Owner: user. Sets when office managers' check on the live app must be done.
- Open question: Retention and data protection for staff names and attendee lists (initiative OQ-3); Litestream keeps copies off the host. Owner: user. Needed before go-live.
- Open question: How real rooms reach the live app: load HR's list first, then office managers enter and check their rooms, or another order (architecture Environments seeds production with the made-up build seed). Owner: user. Settle when this epic is refined.
- Open question: Where integrated verification on the deployed app runs, since there is no staging (architecture Deferred): a separate database on the host, a read-only smoke check, or a run that cleans up after itself. Owner: user. Settle when this epic is refined; epics 2 and 3 follow the answer.
- Architecture: the spine's scope line and Deferred notes still name epic-offices-and-rooms for the host stand-up and CI; offer `bmad-architecture` to update it.
- Assumption: Only company networks reach the app, since there is no sign-in (architecture AD-11); confirmed with OQ-4.
- Unknown: OQ-4 gates the host stand-up entry; it goes on that entry's `unknown` when it is planned.
- Waits on epic-offices-and-rooms because: it needs the app running locally: scaffold, database, seed command, shell and Manage rooms, and its Playwright suite.
- Decision: 2026-11-12, user: created from epic-offices-and-rooms' deferred deployment work, so that epic closes for running on the user's computer.
- Decision: 2026-11-12: second in build order, so epic-find-and-book can build without waiting on it and needs it only for its own check on the deployed app.
