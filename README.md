# room-booker

> **An example app for the BMad docs walkthroughs.** BMad skills in Claude Code built all of it: the planning documents through *Walk Through Three Routes*, Part 3, and the rest through quick builds. A reader agent typed each prompt; no code was written by hand.
>
> - [`walkthrough-log/`](walkthrough-log/README.md) has every step: what was typed, what the agent did and replied, wall time and cost. Raw session logs are on the [`transcripts`](https://github.com/ilya-baimetov/bmad-room-booking-app/tree/transcripts) branch.
> - Each story build has its own [pull request](https://github.com/ilya-baimetov/bmad-room-booking-app/pulls?q=is%3Apr+is%3Amerged).
> - The [`brownfield-start`](https://github.com/ilya-baimetov/bmad-room-booking-app/tree/brownfield-start) tag is this app with every BMad file removed: the starting point for *Walk Through an Existing Codebase*.

Company Room Booking: internal room booking for the London, Manchester and Leeds offices.
One FastAPI app, one SQLite file, server-rendered pages with htmx.

## First local run

You need [uv](https://docs.astral.sh/uv/). It installs Python 3.14 for you if it is missing.

Run these from the repository root, in order:

```sh
uv sync                                     # install Python 3.14 and dependencies
uv run alembic upgrade head                 # create the database in var/roombooker.db
uv run python -m roombooker.seed seeds/build-people.csv --demo-bookings
                                            # load the made-up offices and people, plus demo rooms and bookings
uv run uvicorn roombooker.app:app           # serve the app
```

Leave out `--demo-bookings` to start with no rooms or bookings (see [Demo bookings](#demo-bookings)).

Open <http://127.0.0.1:8000/>. You land on Pick your name; type part of a name and pick it.
Your name then shows in the top bar; tap it to switch to someone else. Everyone except office
managers lands on Rooms; office managers land on Manage rooms. The tabs at the top move between
Rooms, My bookings and, for office managers, Manage rooms.

## Booking a room

On **Rooms**, pick a date, a start time, a length (15 minutes to 4 hours, in 15-minute steps) and,
if you like, how many people the room must seat, then **Find rooms**. You see:

- **Free** rooms for that slot, grouped by office, your own office first. Tap **Book** on one.
- **Booked then**: every booking that overlaps the slot, in any office.
- **Your upcoming bookings**: the bookings you made that have not ended yet.

On the booking form, give the booking a title (up to 100 characters) and, optionally, add attendees
by typing part of their name. **Book** saves it and opens the booking.

The rules: bookings start on the hour or at 15, 30 or 45 minutes past, can't start in the past or
more than 90 days ahead, and never overlap another booking in the same room (two people booking the
same slot at once get one booking and one refusal). Closed rooms can't be booked.

Anyone can open a booking. Its attendees are shown only to the person who booked it, its attendees
and the room's office managers. Only the person who booked it can **Cancel booking**, and only
until it ends.

Office managers add, rename, resize, close and reopen their own office's rooms on **Manage rooms**.
Closing a room cancels its bookings that have not started yet.

## My bookings

**My bookings** shows the bookings you made or were invited to, in a **Day** or **Week** view.
**Previous** and **Next** step a day or a week; **Today** comes back to now, and today is
highlighted. On a phone the week is a list of days. Tap a booking to open it.

## Demo bookings

`--demo-bookings` on the seed command adds demo data after loading people, so the app has something
to show on a first run:

- **Rooms**: Thames, Fleet, Kingsway and Booth 1 in London; Irwell, Deansgate and Ancoats in
  Manchester; Aire, Briggate and Kirkgate in Leeds, added as each office's manager.
- **Bookings**: about 60 across all three offices, on the weekdays of this week and next, dated
  from the day you run the command (Monday of this week to Friday of next week, UK time). There is a
  daily 09:30 stand-up in each office plus planning meetings, 1:1s, workshops and reviews, some
  booked by people from another office. Every booking is made by and invites people from
  `seeds/build-people.csv`, and every one of them is in at least one booking.

Earlier days of this week are filled too, so the week view looks lived-in; those bookings have
already happened and can't be cancelled. Running the command again is safe: rooms that already exist
are kept and bookings whose slot is already taken are skipped. To move the bookings to a new week,
rerun it then (older weeks stay), or start again with an empty database:

```sh
rm var/roombooker.db
uv run alembic upgrade head
uv run python -m roombooker.seed seeds/build-people.csv --demo-bookings
```

The demo needs the build seed's people. With any other file the command loads the people, then
exits non-zero with `error: demo bookings need the build seed: ...` and writes no demo data.
Never use `--demo-bookings` with HR's list.

## Loading people

The same command loads the build seed and HR's list:

```sh
uv run python -m roombooker.seed path/to/people.csv
```

The CSV has the columns `email,name,office,office_manager`. Offices are created by name.
`office_manager` is `true`, `yes` or `1` for an office manager, and `false`, `no`, `0` or blank otherwise.
People are matched on email: a reload updates them in place, and anyone missing from the file is
marked inactive (never deleted), so everyone keeps their id. If any row is wrong, nothing is loaded
and the command exits non-zero, naming the line and the problem.

## Settings

| Variable | Default | Meaning |
| --- | --- | --- |
| `ROOMBOOKER_DB_PATH` | `var/roombooker.db` | SQLite file; its folder is created if missing |
| `ROOMBOOKER_ENV` | `local` | `production` marks the name cookie `Secure` (HTTPS only) |

## Tests

There are two suites. `tests/*.py` test the rules, pages and seed command against a temporary
database in a few seconds. `tests/e2e/` starts the real app with the commands above (migrate,
seed, uvicorn) on a free port and drives it in Chromium at laptop (1280 px) and phone (390 px)
widths. Neither touches `var/roombooker.db`.

```sh
uv sync                                         # once: includes pytest and Playwright
uv run playwright install chromium              # once, for the browser tests
uv run pytest                                   # everything
uv run pytest --ignore=tests/e2e                # without the browser tests
uv run pytest tests/e2e                         # only the browser tests
uv run pytest tests/test_demo.py                # one file
uv run pytest -k "phone"                        # tests whose name matches, e.g. one width
uv run pytest tests/e2e --headed --slowmo 300   # watch the browser tests run
```

## Schema changes

Every table change is an Alembic migration in `migrations/versions/`; run `uv run alembic upgrade head`
before starting the app.
