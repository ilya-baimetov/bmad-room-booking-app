# Part 2: build story 1

Label `b2-story1-build`. 
5 turns, 11 min 9 s wall time, $4.04. Session: [`b8158ca3`](https://github.com/ilya-baimetov/bmad-room-booking-app/blob/transcripts/brownfield/raw/b8158ca3-88fe-4486-a81d-f84125e0870c.jsonl).


## Turn 1

**You typed:**

````text
/bmad What's next?
````

<details><summary>What the agent did (8 tool calls)</summary>

```text
$ ls .claude/skills; uv run .claude/skills/bmad/scripts/knowledge.py --content --root .claude/skills 2>&1 | head -c 60000
Read /home/claude/runs/inherited/.claude/skills/bmad/references/help.md
$ python3 -c "
Read /root/.claude/projects/-home-claude-runs-inherited/b8158ca3-88fe-4486-a81d-f84125e0870c/tool-results/bmf7couo0.txt
$ ls -a; ls _bmad 2>&1; git log --oneline | head -15; git status --short | head
$ uv run _bmad/scripts/resolve_config.py --project-root . --key core.output_folder --key core.active_initiative 2>&1 | grep -v UV_NATIVE; find _bmad-output -type f | head -50
Read /home/claude/runs/inherited/_bmad-output/initiative-calendar-export/initiative-calendar-export.md
Read /home/claude/runs/inherited/_bmad-output/initiative-calendar-export/tickets/tickets.toml
```

</details>

**Reply** (29 s, $0.39):

Hi Ilya, I'm BMad. Your active initiative is **calendar-export**. The spec is written and sliced into two stories, and neither has a build plan yet. Next step:

**Build story 1, "Add to calendar downloads a booking as an .ics file", with `bmad-build`.**

Why this one first:
- **It's the only story that's ready.** Story 2 (the private feed) has `after = [1]`. Story 1 settles the iCalendar event format and the UK-time handling, and story 2 reuses both.
- **It fits one session.** It covers R1 and C3, the risk is medium, and it touches only the booking details page plus one new download route in `bookings`.
- **It has a manual check (`hitl = true`).** After the build, you need to import the file into Outlook, Google Calendar and Apple Calendar yourself. Plan for a GMT booking and a BST booking. The tests check the UTC times, but they can't check how each app shows them.

I'd run it in a fresh context: `/bmad-build` with no arguments picks the next ready entry, which is story 1. Or I can start it here.

**Two things to settle soon:**
1. **The open question in the initiative: can the room booker be reached from the internet?** It doesn't block story 1. It does decide whether story 2 can pass its three-app check, because Google Calendar and Outlook on the web fetch subscribed feeds from their own servers. If the app is internal only, R2 needs a decision before story 2 starts: drop those two apps, or make the feed reachable. Answer it with Sofia (`bmad-agent-po`), and she'll record it as a dated Decision.
2. **Uncommitted files.** `_bmad-output/plan-book-again.md` belongs to the "Book again" feature, which is already committed in `36d0004`. `_bmad/`, `.claude/` and `skills-lock.json` are also untracked. Decide whether to commit them or ignore them before the next build's commit. Otherwise they'll get mixed into it.

After story 1: review happens inside `bmad-build`, then you mark the ticket done, then story 2. Story 2's risk is high (secret addresses and serving requests without a cookie), so a `bmad-code-review` or `bmad-walkthrough` pass on it is worth the time.


## Turn 2

**You typed:**

````text
Yes. Start it here. Commit them first.
````

<details><summary>What the agent did (23 tool calls)</summary>

```text
$ git branch -a; git remote -v; cat .gitignore; git show --stat 5f72d52 | head -40; git status --short -uall | head -80; git status --short -uall | wc -l
$ git status --short -uall | grep -v '^?? .claude/skills/'; ls -la _bmad/custom; cat skills-lock.json | head -20; head -20 _bmad-output/plan-book-again.md
$ git add .claude _bmad skills-lock.json && git commit -q -m "chore: install BMad (core-tools and method modules)
Skill bmad-build Story 1 of initiative-calendar-export: "Add to calendar downloads a booking as an .ics file" (tickets.toml entry id 1)
$ uv run --no-cache "/home/claude/runs/inherited/_bmad/scripts/render_skill.py" --project-root "/home/claude/runs/inherited" --skill "/home/claude/runs/inherited/.claude/skills/bmad-
Read /home/claude/runs/inherited/_bmad/render/bmad-build/inherited-226590ecb13f/9a4f85c09f604d26b667/step-01-clarify-and-route.md
$ uv run _bmad/method/scripts/tickets.py --project-root . find 1 2>&1 | grep -v UV_NATIVE; ls _bmad-output/initiative-calendar-export/
Read /home/claude/runs/inherited/_bmad/render/bmad-build/inherited-226590ecb13f/9a4f85c09f604d26b667/step-02-plan.md
$ find roombooker tests migrations -type f -not -path '*/__pycache__/*' | sort | xargs wc -l | sort -k2; cat pyproject.toml
Read /home/claude/runs/inherited/roombooker/core/time.py
Read /home/claude/runs/inherited/roombooker/bookings/web.py
Read /home/claude/runs/inherited/roombooker/bookings/service.py
Read /home/claude/runs/inherited/roombooker/templates/bookings/details.html
$ cat roombooker/core/settings.py roombooker/app.py roombooker/core/identity.py; sed -n 1,60p roombooker/people/store.py; cat roombooker/people/service.py | head -76
Read /home/claude/runs/inherited/_bmad-output/plan-book-again.md
$ cat tests/conftest.py; grep -n "def test_\|book_again\|Book again" tests/test_bookings.py | head -60; sed -n 1,60p tests/test_bookings.py; cat roombooker/core/errors.py
$ sed -n 60,102p tests/test_bookings.py; sed -n 304,352p tests/test_bookings.py; sed -n 1,40p migrations/versions/0003_bookings.py; sed -n 1,50p roombooker/bookings/store.py; ls ~/.c
Read /home/claude/runs/inherited/tests/test_bookings.py
Read /home/claude/runs/inherited/migrations/versions/0003_bookings.py
Read /home/claude/runs/inherited/_bmad/render/bmad-build/inherited-226590ecb13f/9a4f85c09f604d26b667/plan-template.md
SendUserMessage
Wrote /home/claude/runs/inherited/_bmad-output/initiative-calendar-export/tickets/story-add-to-calendar-downloads-a-booking-as-an-ics-file-plan.md
$ wc -w -c _bmad-output/initiative-calendar-export/tickets/story-add-to-calendar-downloads-a-booking-as-an-ics-file-plan.md
```

</details>

**Reply** (129 s, $1.03):

The plan is written and has one open question. Two more things need your answer before I can show the plan for approval.

**1. How should the organiser appear in the event?** The initiative's decision says each event "shows the organiser".
- **A. In the event's description only**, as "Booked by Hannah Okafor". It shows in all three apps, and the file can never turn into a meeting invitation. **I recommend this one.**
- **B. As the formal organiser as well** (an `ORGANIZER` line with their email). Outlook and Apple may then treat the import as an invitation from that person. Anyone who isn't the organiser could see reply buttons or a "not the organizer" warning, and the organiser's email goes into the file.

**2. The plan is long: about 1,900 tokens against the workflow's 1,600 guideline.** It's still one goal (one route, one formatter, one link, and their tests). Most of the length is the iCalendar rules that the coding agent must not get wrong, such as UTC times, line folding and escaping. Splitting it would separate the formatter from the download, and the formatter can't be tested end to end on its own. **I recommend keeping the full plan.**

**3. Subagents.** The plan comes out at more than 100 lines, so the workflow sends implementation to a coding subagent and runs review through subagents. May I use subagents for the rest of this build? If not, I'll do the implementation and review in this session.

Plan file: `_bmad-output/initiative-calendar-export/tickets/story-add-to-calendar-downloads-a-booking-as-an-ics-file-plan.md`

The risk is **medium**, as in the ticket. Nothing writes data and the download is read-only. The main ways it can go wrong are wrong times around a clock change and a file that one of the apps rejects.


## Turn 3

**You typed:**

````text
Go with your picks. Subagents are fine.
````

<details><summary>What the agent did (3 tool calls)</summary>

```text
Edited /home/claude/runs/inherited/_bmad-output/initiative-calendar-export/tickets/story-add-to-calendar-downloads-a-booking-as-an-ics-file-plan.md
Edited /home/claude/runs/inherited/_bmad-output/initiative-calendar-export/tickets/story-add-to-calendar-downloads-a-booking-as-an-ics-file-plan.md
Edited /home/claude/runs/inherited/_bmad-output/initiative-calendar-export/tickets/story-add-to-calendar-downloads-a-booking-as-an-ics-file-plan.md
```

</details>

**Reply** (21 s, $0.11):

I've recorded both answers in the plan's locked section. One step is left before any code: approving the plan.

**What story 1 will do:**
- **Add to calendar link:** a plain link on every booking's details page. It's hidden only while someone is confirming a cancel. It goes to `GET /bookings/<id>/calendar.ics`.
- **The download:** one standard iCalendar event with the title, the start and end in UTC (so each app shows the right UK time in both GMT and BST), the room and office as location, and "Booked by <name>". There are no attendees, so importing it never sends an invitation and never shows names that are hidden on the page.
- **One shared formatter:** a pure function in the new file `roombooker/bookings/ical.py`, which the bookings service calls. Story 2's feed will reuse it.
- **No database changes:** no tables, no migrations, nothing written.
- **Tests:** checks on the file format (escaping, line folding including a multi-byte character, line endings), plus one HTTP test for each row of the plan's edge-case table. That covers a GMT booking, a BST booking, someone else's booking, an unknown id and having no cookie.

**Risk: medium.** It's read-only, so it can't break bookings. The ways it can go wrong are wrong times across a clock change and a file that one of the apps won't import. The second only shows up in your manual check in the three apps.

The plan is about 1,900 tokens; you chose to keep it whole. A plan that long can make the coding agent drift in its later details. The review step will catch that.

Plan: `_bmad-output/initiative-calendar-export/tickets/story-add-to-calendar-downloads-a-booking-as-an-ics-file-plan.md`

---

Before approving, you can open the plan file in an editor or ask me questions and tell me what to change. You can also use `bmad-advanced-elicitation` or `bmad-party-mode`, ideally in another session to avoid context bloat.

---

How do you want to go on?
- **Approve and continue:** I implement it now, in this session.
- **Approve and stop:** the plan is marked ready for development, and a fresh `bmad-build` session picks it up at implementation.
- **Review plan:** a subagent reviews the plan first, and we go through its findings before you approve.


## Turn 4

**You typed:**

````text
Approved.
````

<details><summary>What the agent did (18 tool calls)</summary>

```text
$ P=_bmad-output/initiative-calendar-export/tickets/story-add-to-calendar-downloads-a-booking-as-an-ics-file-plan.md && grep -n "^status\|Open Questions" $P && sed -i "s/^status: dra
Read /home/claude/runs/inherited/_bmad/render/bmad-build/inherited-226590ecb13f/9a4f85c09f604d26b667/step-03-implement.md
$ git rev-parse HEAD
Edited /home/claude/runs/inherited/_bmad-output/initiative-calendar-export/tickets/story-add-to-calendar-downloads-a-booking-as-an-ics-file-plan.md
Subagent: Implement story 1 plan
$ git add -N . && git diff a35097328314f4ca3b390f28367491086b74275a -- . ':!_bmad-output' > /tmp/claude-0/-home-claude-runs-inherited/b8158ca3-88fe-4486-a81d-f84125e0870c/scratchpad/
$ git add -N roombooker tests && git diff a35097328314f4ca3b390f28367491086b74275a -- roombooker tests > /tmp/claude-0/-home-claude-runs-inherited/b8158ca3-88fe-4486-a81d-f84125e0870
Read /tmp/claude-0/-home-claude-runs-inherited/b8158ca3-88fe-4486-a81d-f84125e0870c/scratchpad/story1.diff
$ uv run pytest --ignore=tests/e2e -q 2>&1 | tail -3; uv run pytest tests/e2e -q 2>&1 | tail -3
Read /home/claude/runs/inherited/_bmad/render/bmad-build/inherited-226590ecb13f/9a4f85c09f604d26b667/step-04-review.md
$ sed -i -e "s/^status: in-progress/status: in-review/" -e "s/^review: ''/review: quick/" -e "s/^review_source: ''/review_source: pinned/" -e "s/^lenses_ran: \[\]/lenses_ran: [quick]
Subagent: Quick review of story 1
SendMessage
$ git diff roombooker/bookings/ical.py tests/test_ical.py | head -5; grep -n "def escape" -A8 roombooker/bookings/ical.py; uv run pytest --ignore=tests/e2e -q 2>&1 | tail -1; uv run 
Read /home/claude/runs/inherited/_bmad-output/initiative-calendar-export/tickets/story-add-to-calendar-downloads-a-booking-as-an-ics-file-plan.md
Edited /home/claude/runs/inherited/_bmad-output/initiative-calendar-export/tickets/story-add-to-calendar-downloads-a-booking-as-an-ics-file-plan.md
Read /home/claude/runs/inherited/_bmad/render/bmad-build/inherited-226590ecb13f/9a4f85c09f604d26b667/step-05-present.md
$ sed -i "s/^status: in-review/status: built/" _bmad-output/initiative-calendar-export/tickets/story-add-to-calendar-downloads-a-booking-as-an-ics-file-plan.md && git add roombooker 
```

</details>

**Reply** (454 s, $2.25):

Story 1 is built and committed as `1f90dba`. Every booking's details page now has an **Add to calendar** link that downloads the booking as a one-event `.ics` file. The times are in UTC, so calendar apps show the right UK time in both GMT and BST. Attendees are left out.

Both test suites pass (119 unit, 21 end-to-end). Review found one real problem: stray control characters in a name or title would make the file invalid. It's fixed and covered by a test. Nothing was deferred.

Before the story counts as done, you need to check it by hand: download one winter (GMT) booking and one summer (BST) booking, and import each into Outlook, Google Calendar and Apple Calendar. Each should land as one event at the UK time the details page shows. If all six imports are right, Sofia (`bmad-agent-po`) can mark story 1 done. That unblocks story 2, and the internet-access question needs an answer before story 2's own three-app check.

Pushing is disabled on this checkout, so I can't open a pull request from here. Next you could run `bmad-walkthrough` on `1f90dba`, or start story 2.


## Turn 5

**You typed:**

````text
How do I run the app?
````

<details><summary>What the agent did (4 tool calls)</summary>

```text
$ sed -n 1,80p README.md
$ export ROOMBOOKER_DB_PATH=/tmp/claude-0/-home-claude-runs-inherited/b8158ca3-88fe-4486-a81d-f84125e0870c/scratchpad/try.db && rm -f $ROOMBOOKER_DB_PATH && uv run alembic upgrade he
Wrote /tmp/claude-0/-home-claude-runs-inherited/b8158ca3-88fe-4486-a81d-f84125e0870c/scratchpad/bst_booking.py
$ ROOMBOOKER_DB_PATH=/tmp/claude-0/-home-claude-runs-inherited/b8158ca3-88fe-4486-a81d-f84125e0870c/scratchpad/try.db bash -c 'uv run alembic upgrade head -q; uv run python -m roombo
```

</details>

**Reply** (36 s, $0.25):

Run these from the repository root (this is the README's "First local run"):

```sh
uv sync                                    # installs Python 3.14 and dependencies
uv run alembic upgrade head                # creates var/roombooker.db
uv run python -m roombooker.seed seeds/build-people.csv --demo-bookings
uv run uvicorn roombooker.app:app          # serves the app
```

Open http://127.0.0.1:8000/, type part of a name on Pick your name, and pick someone. Open any booking and you'll see **Add to calendar** next to the other buttons.

**For the six-import check, the winter (GMT) file is easy.** The demo bookings fall this week and next, which is GMT, so any of them will do.

**The summer (BST) file needs an extra step.** The app only takes bookings from now to 90 days ahead, and summer time doesn't start until 28 March, so you can't book one in the app. I wrote a script that adds one past booking for Tue 7 Jul 2026, 10:00–11:00 UK time. It goes through `bookings.service` with the seed's `allow_past` option, like the demo data does. Run it after the seed command:

```sh
uv run python /tmp/claude-0/-home-claude-runs-inherited/b8158ca3-88fe-4486-a81d-f84125e0870c/scratchpad/bst_booking.py
```

It prints the booking's URL. Open it and download the file. In each of the three apps it should show as 10:00–11:00 on 7 July.

I haven't run the script, because my test run on a scratch database needed a permission I didn't have. It only calls functions I read during the build, but if it errors, send me the output.

If you open the app from your phone or another machine, Apple Calendar can open the file straight from Safari. For Outlook and Google Calendar on the web, use their import option on the downloaded file.
