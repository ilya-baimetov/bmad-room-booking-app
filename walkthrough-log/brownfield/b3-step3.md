# Part 3, step 3: the door screen (UX)

Label `b3-step3`. 
4 turns, 4 min 37 s wall time, $1.75. Session: [`356fbf9f`](https://github.com/ilya-baimetov/bmad-room-booking-app/blob/transcripts/brownfield/raw/356fbf9f-0571-4521-859a-d099fc51e4f9.jsonl).


## Turn 1

**You typed:**

````text
/bmad What's next?
````

<details><summary>What the agent did (8 tool calls)</summary>

```text
$ ls .claude/skills | head -50; uv run .claude/skills/bmad/scripts/knowledge.py --content --root .claude/skills 2>&1 | head -400
Read /home/claude/runs/inherited/.claude/skills/bmad/references/help.md
$ python3 -c "
Read /root/.claude/projects/-home-claude-runs-inherited/356fbf9f-0571-4521-859a-d099fc51e4f9/tool-results/bl3rj56kt.txt
$ ls _bmad; cat _bmad/config.toml
$ uv run _bmad/scripts/resolve_config.py --project-root . --key core.output_folder --key core.active_initiative 2>/dev/null; ls -la _bmad-output 2>&1; find _bmad-output -maxdepth 4 2
Read /home/claude/runs/inherited/_bmad-output/initiative-check-in/initiative-check-in.md
$ cd /home/claude/runs/inherited/_bmad-output && cat initiative-check-in/.memlog.md; echo ----; head -40 research-booking-lifecycle-and-end/research-booking-lifecycle-and-end.md; ech
```

</details>

**Reply** (30 s, $0.42):

Hi, I'm the BMad Agent. I checked where the project stands. Here's the next step.

**Active initiative:** `initiative-check-in`, "Booked rooms nobody turns up to are freed for others". Calendar export is finished (both stories built and closed), and Book again has shipped.

**Where check-in is:** the initiative file is written. It has R1–R7, C1–C6 and Done when, and both of Sofia's validation passes came out clean. There are no open questions. The one assumption, that anyone can check in a booking, was accepted. It is marked `risk: high`. **It hasn't been split into epics yet.** There is no `tickets/` folder.

## Next: ask Sofia to split it into epics

Run `bmad-agent-po` and say **"slice this initiative"**. She writes short epics, each marked `refined: false`. The Boundaries section already suggests a split, roughly one epic each for rooms (tablet setup, freed count), bookings (check-in, freeing) and calendar (freed status on My bookings and in the feed). The tracer path gives her the end-to-end thread.

## Then, almost certainly: `bmad-architecture`

After slicing, the method asks whether epics built separately would have to share decisions. Here they would. The research and constraints show that **every epic depends on how "freed" is stored**:

- **C3:** today a booking only stops blocking its slot when its row is deleted, so freeing needs a new state that the overlap triggers and the `begin_immediate` lock still respect.
- **C4:** Python and the SQLite triggers read different clocks, and no test can fake the trigger clock. You need to decide where release happens and how to test it at exactly +15 minutes.
- **C6:** freed bookings must appear as cancelled in the feed without breaking existing UIDs.
- The dependency order (`bookings` → `rooms`) also matters: the rooms-side freed count can't call into bookings.

If these are left to each epic, the bookings, rooms and calendar epics will each invent their own answer. Run `bmad-architecture` on the initiative, then have Sofia adopt the result as a companion the epics cite. After that comes refining each epic, then planning its stories, then `bmad-build` per story.

## One housekeeping item

`_bmad-output/research-booking-lifecycle-and-end/` is **not in git**, but the initiative lists it as a source. Commit it before slicing so the spec's sources are on the branch. I haven't touched it.

I'd run Sofia in a fresh context. Or I can start `bmad-agent-po` here if you prefer.


## Turn 2

**You typed:**

````text
I'd like to design the door screen with UX first. Start it here.
````

<details><summary>What the agent did (13 tool calls)</summary>

```text
Skill bmad-ux Design the door screen (room tablet page) for the active initiative initiative-check-in: _bmad-output/initiative-check-in/initiative-check-in.md (R1–R3, R7, C1, C2, C5). Not yet sliced into epics.
$ uv run _bmad/scripts/resolve_customization.py --skill .claude/skills/bmad-ux --project-root . --key workflow 2>/dev/null; ls _bmad-output/initiative-check-in; ls _bmad-output/ux-* 
$ ls roombooker/templates roombooker/templates/* roombooker/static 2>/dev/null | head -60; wc -c roombooker/static/*.css 2>/dev/null
Read /home/claude/runs/inherited/_bmad-output/initiative-check-in/sources/request-2026-11-13.md
Read /home/claude/runs/inherited/roombooker/static/tokens.css
Read /home/claude/runs/inherited/roombooker/templates/base.html
$ git ls-files | grep -iE 'design|experience|ux' ; ls docs docs/*
$ W=_bmad-output/initiative-check-in/ux-door-screen && mkdir -p $W/.working $W/imports && uv run _bmad/scripts/memlog.py init --workspace $W --field topic="Door screen: room tablet p
$ cd /home/claude/runs/inherited/_bmad-output/initiative-check-in && mkdir -p ux-door-screen/.working ux-door-screen/imports && uv run ../../_bmad/scripts/memlog.py init --workspace 
Wrote /home/claude/runs/inherited/_bmad-output/initiative-check-in/ux-door-screen/DESIGN.md
Wrote /home/claude/runs/inherited/_bmad-output/initiative-check-in/ux-door-screen/EXPERIENCE.md
Wrote /home/claude/runs/inherited/_bmad-output/initiative-check-in/ux-door-screen/ux-door-screen.md
$ mkdir -p /home/claude/runs/inherited/_bmad-output/initiative-check-in/ux-door-screen/.working /home/claude/runs/inherited/_bmad-output/initiative-check-in/ux-door-screen/imports &&
```

</details>

**Reply** (48 s, $0.35):

The UX workspace is ready at `_bmad-output/initiative-check-in/ux-door-screen/`. Now I need your input.

I'm running **bmad-ux** to design the door screen. Two tools are available at any point: say **"party mode"** to have Sally, Winston and the others argue a decision out, or **"advanced elicitation"** to push a draft past its first answer.

**What I'm working from:** the initiative's R1–R3 and R7, plus C1 (no QR codes, sensors or notifications), C2 (an ordinary tablet showing a web page) and C5 (every page works as a full page load). The app already has a visual identity in `roombooker/static/tokens.css`: navy `#1B2A4A`, system-ui type, 44px touch targets and slot styles for free, booked and closed. The DESIGN.md it was built from is no longer in the repo.

The ticket doesn't settle these points, so I need your answers:

1. **Visual identity.** Should the door screen use the app's existing tokens, or does a screen read from across a corridor need its own look? This is your decision. I won't suggest a direction.
2. **The device.** What tablet is it, roughly what screen size, and is it portrait or landscape? Is it wall-mounted at eye height or on a stand? How far away is someone when they first glance at it?
3. **A real moment at the door.** Tell me about one specific person arriving for a meeting. Give them a name and a room, and say whether they're on time or late, alone or with others. What do they need to see first, and what's the moment that matters most?
4. **The setup moment (R1).** Is the office manager's one-time setup part of this design, or only the screen after setup? If it's in scope, where does the manager start: on the tablet itself, or from Manage rooms?
5. **What the screen shows between bookings.** Is the room free, is the next booking coming up, or is the day over? Should anything show from across the room, such as a big "Free" or "In use" status, or is it just today's list?
6. **Booking titles.** Today's bookings include their titles. Is it fine for a corridor screen to show titles, or should some be hidden?
7. **Working mode.** Pick one:
   - **Fast path:** I draft both documents now with `[ASSUMPTION]` tags and you correct them.
   - **Coaching path:** we go through it decision by decision, with wireframes and mocks as we go.

Rough answers are fine, and "you decide" is a valid answer to anything except 1.


## Turn 3

**You typed:**

````text
Let's go fast. Design the door tablet's check-in screen, and the check-in and freed states in My bookings.

The tablet is read from a few steps away: the room name, free or booked, and the current booking big enough to see from the door.

Checking in is one tap.

Keep the app's existing look.
````

<details><summary>What the agent did (14 tool calls)</summary>

```text
$ M=/home/claude/runs/inherited/_bmad/scripts/memlog.py; W=/home/claude/runs/inherited/_bmad-output/initiative-check-in/ux-door-screen
Read /home/claude/runs/inherited/.claude/skills/bmad-ux/references/design-md-spec.md
Read /home/claude/runs/inherited/.claude/skills/bmad-ux/assets/design-example-shadcn.md
Read /home/claude/runs/inherited/.claude/skills/bmad-ux/assets/experience-example-shadcn.md
Read /home/claude/runs/inherited/roombooker/templates/calendar/my_bookings.html
Read /home/claude/runs/inherited/roombooker/templates/bookings/_item.html
Read /home/claude/runs/inherited/roombooker/templates/bookings/details.html
Read /home/claude/runs/inherited/roombooker/static/app.css
$ uv run /home/claude/runs/inherited/_bmad/scripts/memlog.py append --workspace /home/claude/runs/inherited/_bmad-output/initiative-check-in/ux-door-screen --type decision --text "Wo
Grep Room|room
Read /home/claude/runs/inherited/roombooker/demo.py
Wrote /home/claude/runs/inherited/_bmad-output/initiative-check-in/ux-door-screen/DESIGN.md
Wrote /home/claude/runs/inherited/_bmad-output/initiative-check-in/ux-door-screen/EXPERIENCE.md
$ uv run /home/claude/runs/inherited/_bmad/scripts/memlog.py append --workspace /home/claude/runs/inherited/_bmad-output/initiative-check-in/ux-door-screen --type event --text "Fast-
```

</details>

**Reply** (170 s, $0.80):

Both documents are drafted in `_bmad-output/initiative-check-in/ux-door-screen/`: `DESIGN.md` (how it looks) and `EXPERIENCE.md` (how it works). They're still marked `draft`, because I filled some gaps myself and need you to check them.

**The door screen**
- It's full screen with no top bar and no links out. The room name, "Free"/"Booked" and the current booking use a new set of large sizes made to be read from the door.
- The app's existing colours carry the state: a navy panel means booked, a white panel means free. Grey means closed or freed, as in "out of use", never red. No new colours.
- It has one control, a 96px **Check in** button. It shows only from 5 minutes before the start to 15 minutes after. Tapping it shows "✓ Checked in", with no confirm step and no name.
- When check-in is open, it shows a fixed time, "Freed at 10:15 if nobody checks in", rather than a ticking timer.
- Once a booking is freed, the panel turns white and shows "Freed: nobody checked in · Free until 15:00".
- It covers about 14 states, including back-to-back bookings, a tap just after the window closes, two people tapping at once, a lost connection, a closed room and a tablet that isn't set up.

**My bookings and details**
- Rooms with a tablet get a tag on each booking: "Check in at the door, 09:55–10:15", "Checked in" or "Freed: nobody checked in".
- A freed booking turns grey. Its details page hides Cancel and keeps Book again.
- Rooms without a tablet look exactly as they do today.

**Assumptions to confirm or correct**
1. The tablet is about 10 inches, in landscape. The large text sizes (88/48/40px) still need checking on a real device from 2–3 m.
2. Check-in can't be undone.
3. A freed booking hides Add to calendar.
4. **Attendees** see the freed and checked-in states too, not only the organiser. If they didn't, they'd walk to a room that's been given away.
5. The screen refreshes every 30 s, so a state change can show up to 30 s late. The server still refuses a check-in after +15 minutes.
6. Booking titles show on the door screen. Organiser names don't.

**Not designed here, as you scoped it:** tablet setup (R1), the weekly freed count (R6), and whether a freed booking still appears in the Rooms page's list. Something will have to cover these before the initiative is done.

**Before I finish, two choices:**
- **Mocks:** should I render an HTML mock of the door screen (booked with check-in open, checked in, freed) and of a freed booking in My bookings? I'd do the door screen at least, since the layout matters most there.
- **Review:** do you want a review before finishing? Options are the checklist walk-through, an accessibility pass, both, or none.

Answer however suits you, for example "1–6 fine, mock the door screen, no review".


## Turn 4

**You typed:**

````text
1–6 fine. No.
````

<details><summary>What the agent did (8 tool calls)</summary>

```text
Edited /home/claude/runs/inherited/_bmad-output/initiative-check-in/ux-door-screen/EXPERIENCE.md
Edited /home/claude/runs/inherited/_bmad-output/initiative-check-in/ux-door-screen/DESIGN.md
Edited /home/claude/runs/inherited/_bmad-output/initiative-check-in/ux-door-screen/DESIGN.md
$ grep -rn "ASSUMPTION" /home/claude/runs/inherited/_bmad-output/initiative-check-in/ux-door-screen/*.md; uv run /home/claude/runs/inherited/_bmad/scripts/memlog.py append --workspac
Edited /home/claude/runs/inherited/_bmad-output/initiative-check-in/ux-door-screen/DESIGN.md
Edited /home/claude/runs/inherited/_bmad-output/initiative-check-in/ux-door-screen/EXPERIENCE.md
Edited /home/claude/runs/inherited/_bmad-output/initiative-check-in/ux-door-screen/ux-door-screen.md
$ uv run /home/claude/runs/inherited/_bmad/scripts/memlog.py append --workspace /home/claude/runs/inherited/_bmad-output/initiative-check-in/ux-door-screen --type event --text "spine
```

</details>

**Reply** (29 s, $0.17):

The door screen UX is final. All six assumptions are now written into the documents as decisions, and everything is marked `status: final`.

Files are in `_bmad-output/initiative-check-in/ux-door-screen/`:
- `DESIGN.md`: how it looks
- `EXPERIENCE.md`: how it works
- `ux-door-screen.md`: index of the two
- `.memlog.md`: decision log

**Skipped because you said no:**
- There are no mocks, so the build will work from the two documents alone.
- The final structure-and-prose review was also skipped, since you declined review.

**Still to check before building:** read the 88/48/40px text sizes on a real tablet from 2–3 m. That's noted in `DESIGN.md`.

**Next: Sofia (`bmad-agent-po`) updates the initiative.** Say *"I added UX for the door screen, update the initiative."* She'll add this folder to the initiative as a companion and bring each difference from the spec to you to fix or ignore. Some decisions here go further than the current requirements:
- attendees see freed bookings too, while R5 names only the organiser;
- a freed booking hides Add to calendar;
- the 30-second refresh lag.

**After that**, the route from before still applies: Sofia splits the initiative into epics, then `bmad-architecture`. Architecture now also has to settle how the door page finds out which room a tablet belongs to, since the screen has no sign-in.

**Not covered yet:** tablet setup (R1), the weekly freed count (R6), and freed bookings in the Rooms page list. These can be another UX run later, or Sofia can leave them to the epics.

Nothing is committed. The new UX folder and the research folder are both untracked in git.
