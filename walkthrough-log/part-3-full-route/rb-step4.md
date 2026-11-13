# Step 4: the UX design

Label `rb-step4`. 
4 turns, 4 min 37 s wall time, $1.69. Session: [`17108c20`](https://github.com/ilya-baimetov/bmad-room-booking-app/blob/transcripts/greenfield/part-3-full-route/raw/17108c20-9bc0-481c-aa86-064c57906c21.jsonl).


## Turn 1

**You typed:**

````text
/bmad What's next?
````

<details><summary>What the agent did (1 tool calls)</summary>

```text
$ uv run .claude/skills/bmad/scripts/knowledge.py --content --root .claude/skills 2>/dev/null | python3 -c "import json,sys;d=json.load(sys.stdin);print('problems:',d['problems']);pr
```

</details>

**Reply** (11 s, $0.11):

BMad here.

**Where you stand:** `initiative-company-room-booking` is active, and the brief and the PRD are both final. There's no UX work yet. The initiative file still holds only its frontmatter, and there are no tickets.

**Next: UX with `bmad-ux`. That's step 3 of 8 on your path.**

Why now: the method lets UX run before or after a PRD, and you chose after. Running it before Sofia means she writes the initiative from all three inputs (brief, PRD and UX) in one pass. Otherwise she'd have to update it again when UX lands. `bmad-ux` writes `DESIGN.md` (how the app looks) and `EXPERIENCE.md` (how it behaves) under `ux-company-room-booking/`. It can also produce wireframes or mocks.

**Have one answer ready:** OQ-2 in the PRD. Can everyone see every booking's title and attendees, or only that a room is taken? With no login, this decides what every screen shows, so settle it at the start of the UX session.

**After that:** Sofia (`bmad-agent-po`) writes the initiative, then slices it into epics. Then come architecture, stories and build.

UX works best in a fresh context, where you'd say "let's create UX design". Or I can start it here now. Which do you prefer?


## Turn 2

**You typed:**

````text
Yes, start it here.
````

<details><summary>What the agent did (7 tool calls)</summary>

```text
Skill bmad-ux Create the UX for the active initiative company-room-booking. This is step 3 of the user's full path (brief → PRD → UX → initiative → epics → architecture → stories → build). Inputs: the final brief at _bmad-output/initiative-company-room-booking/brief-company-room-booking/brief-company-room-booking.md and the final PRD at _bmad-output/initiative-company-room-booking/prd-company-room-booking/prd-company-room-booking.md, each with a .memlog.md beside it. Settle PRD OQ-2 first (can everyone see every booking's title and attendees, or only that a room is taken?), since it decides what every screen shows. Release one: no login (pick your name), web on laptop and phone, three offices (London, Manchester, Leeds), 10–15 rooms each, built-in day and week calendar, overlaps never allowed. The stack is Python with FastAPI and SQLite. The user prefers the fast path. Interactive: the user is present. No tickets exist yet.
$ uv run _bmad/scripts/resolve_customization.py --skill .claude/skills/bmad-ux --project-root . --key workflow 2>/dev/null; uv run _bmad/scripts/resolve_config.py --project-root . --
$ mkdir -p _bmad-output/initiative-company-room-booking/ux-company-room-booking/.working _bmad-output/initiative-company-room-booking/ux-company-room-booking/imports && uv run _bmad/
Wrote /home/claude/runs/room-booker/_bmad-output/initiative-company-room-booking/ux-company-room-booking/DESIGN.md
Wrote /home/claude/runs/room-booker/_bmad-output/initiative-company-room-booking/ux-company-room-booking/EXPERIENCE.md
Wrote /home/claude/runs/room-booker/_bmad-output/initiative-company-room-booking/ux-company-room-booking/ux-company-room-booking.md
$ python3 /tmp/claude-0/-home-claude-runs-room-booker/17108c20-9bc0-481c-aa86-064c57906c21/scratchpad/log.py _bmad-output/initiative-company-room-booking/ux-company-room-booking \
```

</details>

**Reply** (38 s, $0.30):

I'm your UX facilitator for Company Room Booking. Two tools are there whenever you want them: `bmad-party-mode` brings in several agents' views, and `bmad-advanced-elicitation` pushes a draft further.

The workspace is `_bmad-output/initiative-company-room-booking/ux-company-room-booking/`. It holds `DESIGN.md` for how the app looks and `EXPERIENCE.md` for how it works. Both are empty for now.

**Sources.** There's no ticket with Requirements yet, so I'm working from these two. Confirm they're the right ones, or add any I've missed:
- `brief-company-room-booking/brief-company-room-booking.md` (final)
- `prd-company-room-booking/prd-company-room-booking.md` (final)

The PRD already settles a lot: what each screen has to do (FR-1 to FR-14), no login, laptop and phone, three offices, and the day and week calendar. So I'll only ask what's still open on the UX side. **Fast path**, as you like it: one batch of questions, then I draft both documents and tag every guess `[ASSUMPTION]`.

1. **Who sees what (PRD OQ-2).** This one shapes every screen. Can anyone see every booking's **title and attendees**, or only that a room is **taken** (and by whom)? Or something in between?
2. **Look and feel.** Do you have anything to match: company colours, a logo, a font, or a UI kit you want to build on? Or is there an app your staff already like the feel of? If nothing comes to mind, say "plain", and I'll keep it neutral rather than invent a brand.
3. **Phone or laptop first.** Both have to work, but which do people mostly use when they book? That decides which one I design for first.
4. **Finding a free room.** In your own words, what should someone see once they've picked an office, a date and a time? Describe it however it comes to mind, even roughly.
5. **One real booking.** Pick a real person (a first name is enough) and walk me through a booking they'd make: where they are, what device they're on, and what they need. I'll build the main flows from it. If you skip this, I'll use the PRD's journeys and mark them as assumptions.

Anything else the experience has to carry? For example accessibility needs, dark mode, or languages other than English.


## Turn 3

**You typed:**

````text
Let's go fast. It's an internal tool.

Main screen: today's rooms in my office, free and booked, like a calendar.

Booking takes three taps or fewer.

On a phone, show the next free rooms as a list, not a calendar.

A My bookings calendar for each person, by day and by week.

An admin screen for office managers to manage rooms.

Use our company colors: navy and white.

Those sources are right. On who sees what: anyone can see a booking's title and who booked it. It's an internal tool.
````

<details><summary>What the agent did (11 tool calls)</summary>

```text
$ python3 /tmp/claude-0/-home-claude-runs-room-booker/17108c20-9bc0-481c-aa86-064c57906c21/scratchpad/log.py _bmad-output/initiative-company-room-booking/ux-company-room-booking \
Read /home/claude/runs/room-booker/.claude/skills/bmad-ux/references/design-md-spec.md
Read /home/claude/runs/room-booker/.claude/skills/bmad-ux/assets/design-example-shadcn.md
Read /home/claude/runs/room-booker/.claude/skills/bmad-ux/assets/experience-example-shadcn.md
Read /home/claude/runs/room-booker/.claude/skills/bmad-ux/assets/experience-example-mobile.md
Read /home/claude/runs/room-booker/.claude/skills/bmad-ux/assets/design-example-mobile.md
Read /home/claude/runs/room-booker/.claude/skills/bmad-ux/assets/design-example-editorial.md
Wrote /home/claude/runs/room-booker/_bmad-output/initiative-company-room-booking/ux-company-room-booking/DESIGN.md
Wrote /home/claude/runs/room-booker/_bmad-output/initiative-company-room-booking/ux-company-room-booking/EXPERIENCE.md
$ for f in DESIGN EXPERIENCE; do python3 /tmp/claude-0/-home-claude-runs-room-booker/17108c20-9bc0-481c-aa86-064c57906c21/scratchpad/docstats.py _bmad-output/initiative-company-room-
$ python3 /tmp/claude-0/-home-claude-runs-room-booker/17108c20-9bc0-481c-aa86-064c57906c21/scratchpad/docstats.py _bmad-output/initiative-company-room-booking/ux-company-room-booking
```

</details>

**Reply** (144 s, $0.75):

Both documents are drafted, with nothing confirmed yet beyond what you told me.

- `DESIGN.md`: 741 words. Navy and white tokens, the four slot looks (free, booked, mine, closed), 44px tap targets.
- `EXPERIENCE.md`: 1,889 words. Six screens: pick your name, Rooms, the booking sheet, booking details, My bookings, and Manage rooms. Every PRD feature, FR-1 to FR-14, has a screen, and every screen is reached by one of the four flows.

**Your decisions are all in.** The main screen shows today's rooms in your office as a calendar. A phone shows a list instead. Booking takes **2 taps**. There's a My bookings calendar by day and week, and Manage rooms for office managers. Title and organiser are visible to everyone (PRD OQ-2, now settled).

**23 guesses are tagged:** 5 in DESIGN.md and 18 in EXPERIENCE.md, 7 of them in Component Patterns. These matter most:

1. **The title is prefilled as "{Name}'s meeting" and the length defaults to 30 minutes.** That's what makes 2 taps possible. Make the title blank instead and every booking needs typing.
2. **Attendees are visible only to the organiser, the attendees and that office's managers.** You named title and organiser as public, not attendees.
3. **The grid runs from 07:00 to 20:00.** Rooms are rows and time runs across in 15-minute columns.
4. **The exact navy is a placeholder (`#1B2A4A`).** Send the real hex if you have it.

Three quick choices before I finalize:

- **Assumptions:** go through the four above, or leave all 23 tagged for Sofia to carry as open questions?
- **Validation:** skip it, which is my default for an internal tool, or run some of these reviewers: rubric walker, accessibility, fresh reader?
- **Mockups:** I'd render HTML mocks of the two screens where layout drives behaviour, the **laptop day grid** and the **phone free-rooms list**. Everything else would be built from the documents alone. Yes, no, or name others?


## Turn 4

**You typed:**

````text
Your suggestions on the four are fine. No to the review and the mock-ups.
````

<details><summary>What the agent did (13 tool calls)</summary>

```text
Edited /home/claude/runs/room-booker/_bmad-output/initiative-company-room-booking/ux-company-room-booking/DESIGN.md
Edited /home/claude/runs/room-booker/_bmad-output/initiative-company-room-booking/ux-company-room-booking/DESIGN.md
Edited /home/claude/runs/room-booker/_bmad-output/initiative-company-room-booking/ux-company-room-booking/DESIGN.md
Edited /home/claude/runs/room-booker/_bmad-output/initiative-company-room-booking/ux-company-room-booking/EXPERIENCE.md
Edited /home/claude/runs/room-booker/_bmad-output/initiative-company-room-booking/ux-company-room-booking/EXPERIENCE.md
Edited /home/claude/runs/room-booker/_bmad-output/initiative-company-room-booking/ux-company-room-booking/EXPERIENCE.md
$ python3 /tmp/claude-0/-home-claude-runs-room-booker/17108c20-9bc0-481c-aa86-064c57906c21/scratchpad/log.py _bmad-output/initiative-company-room-booking/ux-company-room-booking \
Skill bmad-review skill:bmad-review lenses=structure,prose on /home/claude/runs/room-booker/_bmad-output/initiative-company-room-booking/ux-company-room-booking/DESIGN.md and /home/claude/runs/room-booker/_bmad-output/initiative-company-room-booking/ux-company-room-booking/EXPERIENCE.md. Called by bmad-ux at Finalize (polish) as a doc standard; the caller applies the edits directly. Context: internal-tool UX spines. DESIGN.md follows the Google Labs DESIGN.md spec (frontmatter tokens + locked section order); EXPERIENCE.md follows the experience spine. [ASSUMPTION] tags and PRD id references are intentional. Keep findings to the high-value ones.
$ for f in DESIGN.md EXPERIENCE.md; do uv run .claude/skills/bmad-review/scripts/word_metrics.py _bmad-output/initiative-company-room-booking/ux-company-room-booking/$f 2>/dev/null |
Grep Cancel booking|confirm|No pills
Edited /home/claude/runs/room-booker/_bmad-output/initiative-company-room-booking/ux-company-room-booking/DESIGN.md
Edited /home/claude/runs/room-booker/_bmad-output/initiative-company-room-booking/ux-company-room-booking/EXPERIENCE.md
$ sed -i 's/^status: draft$/status: final/' _bmad-output/initiative-company-room-booking/ux-company-room-booking/DESIGN.md _bmad-output/initiative-company-room-booking/ux-company-roo
```

</details>

**Reply** (84 s, $0.54):

The UX is **final**.

- `_bmad-output/initiative-company-room-booking/ux-company-room-booking/DESIGN.md`: how it looks. Navy and white tokens, the four slot looks, 44px tap targets.
- `_bmad-output/initiative-company-room-booking/ux-company-room-booking/EXPERIENCE.md`: how it works. Six screens, who sees what, states, the 2-tap booking, accessibility, and flows UJ-1 to UJ-4.
- `_bmad-output/initiative-company-room-booking/ux-company-room-booking/ux-company-room-booking.md`: the index naming both. The session log, `.memlog.md`, is in the same folder.

**What's left out, as you chose:** no review and no mockups. Every screen gets built from the documents alone.

**Still open:**
- **18 guesses tagged `[ASSUMPTION]`.** Examples: phone list ordering, the length filter, and confirming before a booking is cancelled. You accepted the four I asked about, and their tags are gone.
- **The real navy hex**, still to supply.
- **What happens to bookings when a room closes**, which the rooms epic decides.

---

BMad here. **Step 3 of 8 is done: UX.**

The UX also settled PRD OQ-2: title and organiser are visible to everyone, attendees only to the people involved.

**Next is step 4: the initiative, with Sofia (`bmad-agent-po`).** She writes the initiative's Requirements and Constraints from three sources: the brief, the PRD's FR and RULE ids, and the UX documents as a companion. She records the unconfirmed assumptions and open questions as Open questions, so they stay visible instead of getting lost. From there she slices the epics, which is step 5.

I recommend running Sofia in a fresh context; there, say "write the initiative from the PRD". Or I can start her here now. Which do you prefer?
