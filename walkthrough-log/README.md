# Walkthrough Log

Every step of the BMad docs walkthroughs that built this app, as it ran. Each log shows the prompt typed, what the agent did, and its reply, with wall time and cost.

- Runs: headless Claude Code with Claude Opus 5.5 and BMad `dev` at `3cf35b6`. Part 3 of Walk Through Three Routes ran at high effort; everything else at the default (medium). A reader agent typed the page's prompts and answered the agents' questions; nothing in the app was written by hand.
- Story builds were merged through pull requests, one per build. Planning steps committed straight to `main`.
- Raw session logs, cleaned of private data, are on the [`transcripts` branch](https://github.com/ilya-baimetov/bmad-room-booking-app/tree/transcripts).

## Part 1: Quick Build

A separate project (a meeting cost timer); its code is not in this repository.

| Step | Turns | Wall time | Cost | Pull request |
| --- | --- | --- | --- | --- |
| [Set up BMad (`/bmad setup`)](part-1-quick-build/g1-setup.md) | 1 | 0 min | $0.33 |  |
| [Part 1: the quick build (meeting cost timer)](part-1-quick-build/g1-step1.md) | 7 | 7 min | $2.75 |  |

Total: 7 min of wall time, $3.07.

## Part 2: Sofia's Route

A separate project (a hobby room booker); its code is not in this repository.

| Step | Turns | Wall time | Cost | Pull request |
| --- | --- | --- | --- | --- |
| [Set up BMad (`/bmad setup`)](part-2-product-owner-route/g2-hobby-setup.md) | 1 | 0 min | $0.27 |  |
| [Part 2, step 1: Sofia writes the requirements and stories](part-2-product-owner-route/g2-step1.md) | 7 | 3 min | $1.48 |  |
| [Part 2, step 2: build story 1](part-2-product-owner-route/g2-step2.md) | 4 | 6 min | $2.57 |  |
| [Part 2, step 3: mark story 1 done](part-2-product-owner-route/g2-step3.md) | 2 | 1 min | $0.68 |  |
| [Part 2: build story 2](part-2-product-owner-route/g2-story2-build.md) | 2 | 3 min | $1.51 |  |
| [Part 2: mark story 2 done](part-2-product-owner-route/g2-story2-done.md) | 2 | 1 min | $0.60 |  |

Total: 16 min of wall time, $7.11.

## Part 3: Full Route

This repository, from the first commit to epic 1 closed.

| Step | Turns | Wall time | Cost | Pull request |
| --- | --- | --- | --- | --- |
| [Set up BMad (`/bmad setup`)](part-3-full-route/rb-setup.md) | 1 | 0 min | $0.27 |  |
| [Step 1: start the initiative](part-3-full-route/rb-step1.md) | 1 | 1 min | $0.99 |  |
| [Step 2: Mary writes the brief](part-3-full-route/rb-step2.md) | 5 | 4 min | $1.12 |  |
| [Step 3: John writes the PRD](part-3-full-route/rb-step3.md) | 5 | 6 min | $2.07 |  |
| [Step 4: the UX design](part-3-full-route/rb-step4.md) | 4 | 4 min | $1.69 |  |
| [Step 5: Sofia writes the requirements and splits them into epics](part-3-full-route/rb-step5.md) | 4 | 7 min | $2.87 |  |
| [Step 6: the architecture](part-3-full-route/rb-step6.md) | 5 | 6 min | $2.19 |  |
| [Step 7: Sofia plans epic 1's stories](part-3-full-route/rb-step7.md) | 6 | 7 min | $2.71 |  |
| [Step 8: build story 1.1, check it, mark it done](part-3-full-route/rb-step8-story1.md) | 7 | 20 min | $7.21 | [#1](https://github.com/ilya-baimetov/bmad-room-booking-app/pull/1) |
| [Step 8: build story 1.2, check it, mark it done](part-3-full-route/rb-step8-story2.md) | 8 | 27 min | $10.64 | [#2](https://github.com/ilya-baimetov/bmad-room-booking-app/pull/2) |
| [Step 9: close the epic, then the retrospective](part-3-full-route/rb-step9.md) | 6 | 15 min | $5.85 |  |

Total: 102 min of wall time, $37.61.

## Finishing the App

Quick builds outside the initiative, to finish the app for the existing-codebase walkthrough. They ran with `route = "oneshot"` and `review = "none"` in a personal settings file, so one agent built each change without a hand-off or a reviewer.

| Step | Turns | Wall time | Cost | Pull request |
| --- | --- | --- | --- | --- |
| [Quick build: find a free room and book it](finishing/rq1-booking.md) | 2 | 14 min | $3.52 | [#3](https://github.com/ilya-baimetov/bmad-room-booking-app/pull/3) |
| [Quick build: the My bookings calendar](finishing/rq2-calendar.md) | 1 | 5 min | $2.09 | [#4](https://github.com/ilya-baimetov/bmad-room-booking-app/pull/4) |
| [Quick build: demo bookings and the README](finishing/rq3-demo.md) | 1 | 5 min | $1.90 | [#5](https://github.com/ilya-baimetov/bmad-room-booking-app/pull/5) |

Total: 25 min of wall time, $7.51.

## Walk Through an Existing Codebase

The same app from the `brownfield-start` branch, cloned with `--depth 1` so no agent could see how it was built, then changed in four parts.

| Step | Turns | Wall time | Cost | Pull request |
| --- | --- | --- | --- | --- |
| [Set up BMad (`/bmad setup`)](brownfield/b-setup.md) | 1 | 0 min | $0.60 |  |
| [Part 0, step 2: the project context](brownfield/b0-context.md) | 5 | 3 min | $0.86 |  |
| [Part 1: the small change (Book again)](brownfield/b1-change.md) | 3 | 12 min | $3.78 | [#6](https://github.com/ilya-baimetov/bmad-room-booking-app/pull/6) |
| [Part 2, step 1: Sofia writes the requirements and stories](brownfield/b2-step1.md) | 6 | 5 min | $1.89 |  |
| [Part 2: build story 1](brownfield/b2-story1-build.md) | 5 | 11 min | $4.04 | [#7](https://github.com/ilya-baimetov/bmad-room-booking-app/pull/7) |
| [Part 2: mark story 1 done](brownfield/b2-story1-done.md) | 2 | 1 min | $0.66 |  |
| [Part 2: build story 2](brownfield/b2-story2-build.md) | 5 | 16 min | $5.84 | [#8](https://github.com/ilya-baimetov/bmad-room-booking-app/pull/8) |
| [Part 2: mark story 2 done](brownfield/b2-story2-done.md) | 2 | 1 min | $0.74 |  |
| [Part 3, step 1: deep recon on how bookings end](brownfield/b3-step1.md) | 3 | 17 min | $8.31 |  |
| [Part 3, step 2: Sofia writes the requirements](brownfield/b3-step2.md) | 5 | 4 min | $2.11 |  |
| [Part 3, step 3: the door screen (UX)](brownfield/b3-step3.md) | 4 | 4 min | $1.75 |  |
| [Part 3, step 4: the architecture](brownfield/b3-step4.md) | 4 | 5 min | $2.04 |  |
| [Part 3, step 5: Sofia plans the stories](brownfield/b3-step5-plan.md) | 9 | 21 min | $8.05 |  |
| [Part 3, step 5: build story 1](brownfield/b3-step5-story1-build.md) | 4 | 15 min | $5.78 | [#9](https://github.com/ilya-baimetov/bmad-room-booking-app/pull/9) |
| [Part 3, step 5: mark story 1 done](brownfield/b3-step5-story1-done.md) | 2 | 1 min | $0.75 |  |

Total: 122 min of wall time, $47.18.

All parts: 275 min of wall time, $102.48.
