# Quick build: demo bookings and the README

Label `rq3-demo`. 
1 turns, 5 min 49 s wall time, $1.90. Session: [`a6f5e5b8`](https://github.com/ilya-baimetov/bmad-room-booking-app/blob/transcripts/greenfield/finishing/raw/a6f5e5b8-ec7c-4c85-aafe-ecb6c7847ace.jsonl).


## Turn 1

**You typed:**

````text
/bmad-build Add demo bookings to the seed: a realistic spread of bookings this week and next across all three offices, made by and inviting the seeded people, loaded by the seed command and dated from the day you run it. Then update the README to cover booking, My bookings, the demo bookings, and how to run the tests. This is loose work, not part of the initiative.
````

<details><summary>What the agent did (47 tool calls)</summary>

```text
$ uv run --no-cache "/home/claude/runs/room-booker/_bmad/scripts/render_skill.py" --project-root "/home/claude/runs/room-booker" --skill "/home/claude/runs/room-booker/.claude/skills
Read /home/claude/runs/room-booker/_bmad/render/bmad-build/room-booker-72ea137e33d5/2b9b11f305ddf3e7d4ac/step-01-clarify-and-route.md
$ git status --short && git branch --show-current && git log --oneline -8 && ls _bmad-output/ _bmad-output/initiative-company-room-booking/ && ls
Read /home/claude/runs/room-booker/_bmad/render/bmad-build/room-booker-72ea137e33d5/2b9b11f305ddf3e7d4ac/step-02-plan.md
$ cat README.md && ls -R roombooker seeds tests | head -80 && cat pyproject.toml
$ cat roombooker/seed.py && ls seeds tests tests/* && head -5 seeds/*.csv && wc -l seeds/*
$ cat seeds/build-people.csv && ls migrations/versions && grep -rn "insert\|Room(" migrations/versions | head; cat roombooker/bookings/service.py roombooker/bookings/store.py
$ cat roombooker/core/time.py && grep -n "^def \|^class \|^[A-Z_]* = " roombooker/rooms/service.py roombooker/people/service.py roombooker/rooms/store.py roombooker/people/store.py r
$ cd /home/claude/runs/room-booker/_bmad-output/initiative-company-room-booking && grep -rn -i "demo\|AD-9\b\|AD-9[^0-9]\|seed" --include=*.md . | grep -v "plan-" | head -30; sed -n 
Grep (?i)demo|AD-9[^0-9]|seed
Read /home/claude/runs/room-booker/roombooker/rooms/service.py
Read /home/claude/runs/room-booker/_bmad/render/bmad-build/room-booker-72ea137e33d5/2b9b11f305ddf3e7d4ac/plan-template.md
$ sed -n 1,200p tests/e2e/conftest.py | grep -n "seed\|alembic\|def " ; grep -n "^def \|^class " roombooker/people/store.py roombooker/people/service.py; sed -n 14,35p roombooker/peo
Grep utc_now|freeze|monkeypatch.setattr\(clock
Grep clock|NOW|datetime\(
Read /home/claude/runs/room-booker/migrations/versions/0003_bookings.py
$ git rev-parse HEAD && date +%F
Wrote /home/claude/runs/room-booker/_bmad-output/initiative-company-room-booking/plan-demo-bookings-seed-and-readme.md
Read /home/claude/runs/room-booker/_bmad/render/bmad-build/room-booker-72ea137e33d5/2b9b11f305ddf3e7d4ac/step-oneshot.md
Read /home/claude/runs/room-booker/roombooker/people/store.py
Read /home/claude/runs/room-booker/roombooker/people/service.py
Edited /home/claude/runs/room-booker/roombooker/people/store.py
Edited /home/claude/runs/room-booker/roombooker/people/service.py
Edited /home/claude/runs/room-booker/roombooker/bookings/service.py
Edited /home/claude/runs/room-booker/roombooker/bookings/service.py
Wrote /home/claude/runs/room-booker/roombooker/demo.py
$ python3 - <<'EOF'
Edited /home/claude/runs/room-booker/roombooker/seed.py
Wrote /home/claude/runs/room-booker/tests/test_demo.py
Edited /home/claude/runs/room-booker/tests/test_demo.py
$ uv run pytest --ignore=tests/e2e -q 2>&1 | tail -15
$ S=/tmp/claude-0/-home-claude-runs-room-booker/a6f5e5b8-ec7c-4c85-aafe-ecb6c7847ace/scratchpad && rm -f $S/demo.db && export ROOMBOOKER_DB_PATH=$S/demo.db && uv run alembic upgrade 
Wrote /tmp/claude-0/-home-claude-runs-room-booker/a6f5e5b8-ec7c-4c85-aafe-ecb6c7847ace/scratchpad/try_demo.sh
$ sh /tmp/claude-0/-home-claude-runs-room-booker/a6f5e5b8-ec7c-4c85-aafe-ecb6c7847ace/scratchpad/try_demo.sh
$ ROOMBOOKER_DB_PATH=var/demo-check.db uv run alembic upgrade head && ROOMBOOKER_DB_PATH=var/demo-check.db uv run python -m roombooker.seed seeds/build-people.csv --demo-bookings
Wrote /tmp/claude-0/-home-claude-runs-room-booker/a6f5e5b8-ec7c-4c85-aafe-ecb6c7847ace/scratchpad/try_demo.py
$ uv run python /tmp/claude-0/-home-claude-runs-room-booker/a6f5e5b8-ec7c-4c85-aafe-ecb6c7847ace/scratchpad/try_demo.py
Read /home/claude/runs/room-booker/tests/e2e/conftest.py
Grep Find a room|Free rooms|>Book<|Cancel booking|Day|Week|Today|<h1|<title
$ sed -n 1,48p roombooker/templates/bookings/rooms.html && grep -n "VIEWPORTS" -A4 tests/e2e/conftest.py | head -6 && grep -n "Previous\|Next\|prev_url\|next_url\|attendees\|Who\|sea
Grep h2|upcoming|Your next|Booked
Edited /home/claude/runs/room-booker/README.md
Edited /home/claude/runs/room-booker/README.md
Grep ROOMBOOKER_DB_PATH|tmp_path_factory
$ uv run pytest -q 2>&1 | tail -4
$ python3 - <<'EOF'
$ git commit -q -F - <<'EOF'
```

</details>

**Reply** (349 s, $1.90):

I added demo bookings to the seed command and rewrote the README. All 115 tests pass, browser tests included. Committed as `a2920a8` on `room-booking`.

- **Demo bookings:** the seed command now takes a `--demo-bookings` flag: `uv run python -m roombooker.seed seeds/build-people.csv --demo-bookings`. After loading people it adds 10 rooms across London, Manchester and Leeds and 58 bookings on the weekdays from Monday this week to Friday next week, counted from the day you run it. There's a daily stand-up in each office plus planning meetings, 1:1s, workshops and some cross-office meetings. Every seeded person organises or is invited to at least one.
- **Reruns are safe:** I ran the command twice on a throwaway database. The second run added nothing.
- **README:** new sections on booking a room, My bookings and the demo bookings. The tests section now explains the two suites and how to run all of them, one file, one screen width, or the browser tests in a visible window. The first-run steps now use the flag.

Decision for you:
- **Opt-in, not automatic:** I put the demo data behind a flag because the same seed command loads HR's real list in production, which should never get fake bookings. The catch is that running the seed without the flag still loads no rooms or bookings. If you'd rather it always load with the build file, it's a small change.
- **Bookings already in the past:** the days of this week that have already gone are filled too, so the week view looks used. To do that, the booking code now has an option to skip the "can't book in the past" rule. Only the demo uses it; the web never does, and the no-overlap and closed-room rules still apply. Those past bookings can't be cancelled.

Review was skipped, as this route sets by default. The plan is in `_bmad-output/initiative-company-room-booking/plan-demo-bookings-seed-and-readme.md`, kept outside the ticket tree. Next I can push and open a PR, walk you through the change with `bmad-walkthrough`, or make another change.
