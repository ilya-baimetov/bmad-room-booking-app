# Part 0, step 2: the project context

Label `b0-context`. 
5 turns, 3 min 8 s wall time, $0.86. Session: [`dea4c3fa`](https://github.com/ilya-baimetov/bmad-room-booking-app/blob/transcripts/brownfield/raw/dea4c3fa-65fc-4672-b022-c9669dde0d3b.jsonl).


## Turn 1

**You typed:**

````text
/bmad-project-context
````

**Reply** (23 s, $0.29):

Setup it is: this repository has no agent instruction file yet.

**What exists (step 1)**
- No `AGENTS.md`, `CLAUDE.md`, Cursor/Copilot rules, or old `project-context.md` (`_bmad-output/` is empty). That makes this **setup**, so there's no ledger to carry over.
- Single unit: one `pyproject.toml` (Python 3.14, FastAPI, SQLAlchemy, Alembic, htmx templates), no workspace members, so there's nothing to ask about scope.
- **No CI config, linter, formatter or hooks.** Anything we want enforced is either prose or a check we add.
- `README.md` is good and up to date. It already covers first run, the test commands (`uv run pytest`, how to split e2e from the rest), settings and migrations. The block won't repeat it.
- `docs/decisions/` holds two ADRs that carry real cross-component rules: casefold matching in Python, not SQLite; closing a room deletes its bookings through a DB trigger. They cite **AD-1, AD-3, AD-4, AD-13** from an architecture document that isn't in the repo.
- History is one squashed commit (`5f72d52`), so there's no history of repeated mistakes to mine.

**What do you bring? (step 2)** Answer whichever apply. "None" is a fine answer.

1. **Rules agents must follow no matter what the code does**: branch or PR rules, frozen paths, data handling (for example, HR's real people list: where it lives and whether agents may ever read or commit it), security or compliance requirements.
2. **Coding standards or style guides** the team follows that aren't written down in the repo.
3. **Outside documents**, as paths or URLs. The main one: where does the architecture document behind AD-1…AD-13 live now? The `greenfield-done` tag mentioned in the last commit? A wiki? Also any handbook or tickets board.

I won't read anything you point me to until the next step. After that I'll scan the code and only ask you about what the scan can't answer.


## Turn 2

**You typed:**

````text
Nothing beyond the repository. Those documents are gone.
````

<details><summary>What the agent did (4 tool calls)</summary>

```text
$ cd /home/claude/runs/inherited/roombooker && cat app.py core/*.py; wc -l */*.py *.py
$ cd /home/claude/runs/inherited && grep -n "^from roombooker\|^import roombooker\|^\s\+from roombooker" roombooker/*/*.py roombooker/*.py | grep -v "^roombooker/app.py"; echo ---; g
$ cat tests/conftest.py tests/e2e/conftest.py | head -150; sed -n 1,60p roombooker/bookings/store.py; grep -n "utc_now\|monkeypatch" tests/*.py | head -15
$ grep -n "utc_now\|setattr" tests/*.py | head; grep -n "utc_now\|datetime.now\|date.today" roombooker -r --include=*.py; sed -n 60,103p migrations/versions/0003_bookings.py; timeout
```

</details>

**Reply** (102 s, $0.26):

Scan done. Here's what I found before the questions:

- **Both suites pass**: `tests/` runs 96 tests in about 7 s; `tests/e2e/` runs 19 browser tests in about 51 s and needs Chromium. The README's commands are correct, so the block won't repeat them.
- **The architecture is still in the code.** Module docstrings state the layering, and the imports match it:
  - web calls only its own service.
  - Each store is imported only by its own service.
  - Each table has a single writing service.
  - Service dependencies run one way: bookings → rooms → people, and calendar → bookings.
  - `core.time` is the only place UTC and UK time are converted; `core.settings` is the only place env vars are read.
  - The schema comes only from Alembic.
  - DB triggers refuse overlapping bookings.
- **31 docstrings cite AD-1…AD-13, RULE-4, R8 and OQ-3.** All of those come from the document you said is gone.
- `core/time.py` says "Tests replace this to fix the clock", but no test does that. Production code does use `utc_now()` consistently.

**Four questions, only about things the scan can't tell me:**

1. **Agent mistakes:** have you seen an agent get something wrong in this repo, or in the greenfield build before it? Anything you remember counts.
2. **Migrations:** is there a deployed database anywhere that has had `0001`–`0003` applied? Put another way, are applied migrations frozen, so changes always go in a new one?
3. **HR's real people list:** is it personal data agents must never commit, copy into `seeds/` or tests, or open? Where does it live?
4. **AD-n citations:** should new code keep citing AD numbers in docstrings, or stop now that the document behind them is gone?


## Turn 3

**You typed:**

````text
1. I don't know yet. I just inherited it.
2. I don't know.
3. I don't know.
4. Those documents are gone.
````

<details><summary>What the agent did (1 tool calls)</summary>

```text
$ grep -n "InvalidRoom\|except\|DomainError" roombooker/*/web.py | head; sed -n 1,12p roombooker/rooms/web.py; grep -n "begin_immediate" -r roombooker --include=*.py; git rev-parse H
```

</details>

**Reply** (35 s, $0.13):

You don't know yet, so the block makes no policy claims and has no pitfalls section. That's on purpose: both need a human to state them or an observed mistake to back them, and I won't make them up. Everything below comes from the code and was checked against it.

## Proposed `AGENTS.md` (new file, the whole contents)

```markdown
<!-- bmad:context -->
<!-- Verified 2026-11-13 against 5f72d52. Managed by bmad-project-context; edits inside this block are replaced on refresh. Keep anything you want preserved outside the markers. -->

## room-booker

Internal room booking for the London, Manchester and Leeds offices: one FastAPI app, one SQLite file, server-rendered Jinja pages with htmx. `README.md` covers running, seeding, settings and tests; `docs/decisions/` holds the two surviving design records.

## Where things are

- Modules `people`, `rooms`, `bookings`, `calendar` under `roombooker/`, each split `web.py` → `service.py` → `store.py`; shared plumbing in `roombooker/core/`.
- Schema and DB triggers: `migrations/versions/`. Seed and demo data: `roombooker/seed.py`, `roombooker/demo.py`.

## Running and verifying

- Run Python only through `uv run`; the project pins Python 3.14 (`pyproject.toml`), which uv installs.
- Iterate with `uv run pytest --ignore=tests/e2e` (~7 s). `tests/e2e` takes ~1 min and needs `uv run playwright install chromium` once.

## Conventions that differ from defaults

- A `web.py` calls only its own module's service; never import another module's service or any `store.py` from a route.
- A `store.py` is imported only by its own service (`people.store` also by `seed.py`); go through the service.
- Service dependencies run one way: `bookings` → `rooms` → `people`, `calendar` → `bookings`. Never import the other way; put cross-module effects in the database (see the room-close trigger) or in the depending service.
- Write `rooms` only via `rooms.service` and `bookings`/`booking_attendees` only via `bookings.service`, including seed and demo code — its `begin_immediate` lock and the overlap triggers in `0003_bookings.py` are what stop double bookings.
- Closing a room deletes its future bookings in the trigger `rooms_close_cancels_future_bookings`; do not also delete them in Python (`docs/decisions/adr-closing-a-room-deletes-its-future-bookings.md`).
- A `Table` in a `store.py` only describes the schema; change tables with a new Alembic migration, never `metadata.create_all`.
- Get the time from `core.time.utc_now()`, never `datetime.now()`; store UTC text `YYYY-MM-DDTHH:MM:00Z`; convert UK↔UTC only in `core.time`.
- Compare names case-insensitively with `str.casefold()` in Python, never SQLite `lower()` or `COLLATE NOCASE` — SQLite folds only ASCII (`docs/decisions/adr-case-insensitive-matching-in-python-not-sqlite.md`).
- Read env vars only through `core.settings.get_settings()`; read the current person only through the `CurrentPerson` dependency.
- Every route must work as a full page load; htmx only narrows the swap with `hx-select`.
- Docstring citations `AD-n`, `RULE-n`, `Rn`, `OQ-n` point to a planning document that no longer exists. Do not search for it, and do not cite new ones; the docstrings and `docs/decisions/` are the record.

<!-- /bmad:context -->
```

**Left out:**
- The README's commands, the settings table and the seed rules: the README already states them correctly.
- A directory tree or stack list.
- Every scan finding I couldn't back with evidence. The clock comment says tests fake time but none do; the ADR notes concurrent case-only room adds can race. Each of those becomes a line only when it turns out to have caused a real mistake.

**Rules I can't write yet:** applied migrations being frozen, HR's people list being personal data, branch and PR rules. Once you know any of these, run `record` or `refresh` and they go in as one-line additions.

**Offer: an automated check.** The three layering lines (web → own service, store → own service, one-way service dependencies) can be enforced by a small pytest test that parses imports, so `uv run pytest` would fail on a violation. There's no CI or linter today, so the test suite is the only place a check would run. If you want it, I'll write it after this file, and a later run can drop those three lines once the test exists.

**Your call:** should I write this `AGENTS.md`, edited or as is? I'll leave it uncommitted. And do you want the layering test?


## Turn 4

**You typed:**

````text
Write it.
````

<details><summary>What the agent did (1 tool calls)</summary>

```text
Wrote /home/claude/runs/inherited/AGENTS.md
```

</details>

**Reply** (19 s, $0.10):

I wrote `AGENTS.md` at the repository root, exactly as you approved it. It isn't committed.

**What went in:** 15 lines, all checked against the code at `5f72d52`:
- **Where things are:** the module layout and where the schema, seed and demo code live.
- **Running and verifying:** run everything through `uv run`, and the fast test loop that skips the browser tests.
- **Conventions:** the layering rules, which service writes which table, the two decision records (room-close trigger, casefold matching), and the rules for time, settings and the current person.
- **The old AD/RULE citations:** a line telling agents not to go looking for the planning document they point to.

**What stayed out, and why:**
- The README already states the commands and settings correctly, and a copy goes stale the first time someone edits one of them.
- There are no policy lines (migrations frozen? HR data rules? branch rules?) because nobody has stated those rules yet.
- There's no pitfalls section because there are no observed agent mistakes yet. The repo has plenty of things that look like traps, but they don't predict real mistakes; only observed ones do.

**Claude Code won't read this file yet.** It loads `CLAUDE.md`, not `AGENTS.md`. Codex, Cursor and others read `AGENTS.md` directly. If you use Claude Code here, add a `CLAUDE.md` containing the single line `@AGENTS.md`. I can create it if you say so.

**Still open:**
- **The layering test:** the pytest import check for the three layering lines. Say the word and I'll write it; a later run then drops those three lines.
- **Rules you learn later:** the moment an agent gets something wrong here, run `/bmad-project-context record`. When you find out about migrations, HR data or branch rules, run `refresh` and they go in as policy lines.
- **Upkeep:** re-run `refresh` after significant changes. It re-checks every path against `5f72d52`.
- **Personal rules:** preferences that are yours rather than the team's belong in your global agent config, not this file.


## Turn 5

**You typed:**

````text
I use Claude Code. Create the CLAUDE.md.
````

<details><summary>What the agent did (2 tool calls)</summary>

```text
$ ls CLAUDE.md .claude/CLAUDE.md 2>&1; git status --short
Wrote /home/claude/runs/inherited/CLAUDE.md
```

</details>

**Reply** (9 s, $0.08):

I created `CLAUDE.md` at the repository root. It contains one line, `@AGENTS.md`, which tells Claude Code to load `AGENTS.md` as its instructions. No `CLAUDE.md` existed before, so nothing was overwritten. Both files are uncommitted.

I haven't seen the import work in a fresh session yet. Two ways to check:
- Start a new Claude Code session here and run `/memory`. Both files should be listed.
- Or ask it a question only the file answers, such as how to compare names case-insensitively.

From now on, edit only `AGENTS.md`. `CLAUDE.md` stays a pointer, so no instruction ends up loaded twice.

The pytest check for the three layering rules is still on offer.
