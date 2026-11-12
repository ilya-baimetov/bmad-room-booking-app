# room-booker

Company Room Booking: internal room booking for the London, Manchester and Leeds offices.
One FastAPI app, one SQLite file, server-rendered pages with htmx.

## First local run

You need [uv](https://docs.astral.sh/uv/). It installs Python 3.14 for you if it is missing.

Run these from the repository root, in order:

```sh
uv sync                                                  # install Python 3.14 and dependencies
uv run alembic upgrade head                              # create the database in var/roombooker.db
uv run python -m roombooker.seed seeds/build-people.csv  # load the made-up offices and people
uv run uvicorn roombooker.app:app                        # serve the app
```

Open <http://127.0.0.1:8000/>. You land on Pick your name; type part of a name and pick it.
Your name then shows in the top bar; tap it to switch to someone else.
You land on Rooms: pick a date, start time and length (15 minutes to 4 hours) to see the free rooms,
your own office first, and book one with a title and attendees. Open a booking to see it; the person
who booked it can cancel it. Bookings can't overlap, start in the past or start more than 90 days ahead.
Office managers land on Manage rooms, where they add, edit, close and reopen their office's rooms.
Closing a room cancels its bookings that have not started yet.

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

```sh
uv run playwright install chromium   # once, for the browser tests
uv run pytest                        # all tests, including browser tests at laptop and phone widths
uv run pytest --ignore=tests/e2e     # without the browser tests
```

## Schema changes

Every table change is an Alembic migration in `migrations/versions/`; run `uv run alembic upgrade head`
before starting the app.
