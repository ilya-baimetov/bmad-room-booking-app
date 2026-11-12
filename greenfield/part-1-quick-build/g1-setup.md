# Set up BMad (`/bmad setup`)

Label `g1-setup`. 
1 turns, 0 min 40 s wall time, $0.33. Session: [`c8c39902`](raw/c8c39902-3693-4145-b599-099f7c3b8e4d.jsonl).


## Turn 1

**You typed:**

````text
/bmad setup
````

<details><summary>What the agent did (12 tool calls)</summary>

```text
Read /home/claude/runs/g1-timer/.claude/skills/bmad/references/setup.md
$ cd /home/claude/runs/g1-timer; which uv; ls -a; ls .claude/skills | head -50; ls ~/.claude/skills 2>/dev/null | head
$ which uv; ls -a /home/claude/runs/g1-timer; ls /home/claude/runs/g1-timer/.claude/skills; ls ~/.claude/skills
$ which uv; ls -a /home/claude/runs/g1-timer; ls /home/claude/runs/g1-timer/.claude/skills
$ uv run --no-cache .claude/skills/bmad/scripts/setup.py --project-root /home/claude/runs/g1-timer --skill /home/claude/runs/g1-timer/.claude/skills/bmad --root /home/claude/runs/g1-
$ uv run --no-cache .claude/skills/bmad/scripts/setup.py --project-root /home/claude/runs/g1-timer --skill /home/claude/runs/g1-timer/.claude/skills/bmad --root /home/claude/runs/g1-
$ uv run --no-cache .claude/skills/bmad/scripts/setup.py --project-root /home/claude/runs/g1-timer --skill /home/claude/runs/g1-timer/.claude/skills/bmad --root /home/claude/runs/g1-
$ uv run --no-cache .claude/skills/bmad/scripts/migrate_v6.py --project-root /home/claude/runs/g1-timer --skill /home/claude/runs/g1-timer/.claude/skills/bmad --root /home/claude/run
Read /home/claude/runs/g1-timer/.claude/skills/bmad/references/migrate.md
$ uv run .claude/skills/bmad/scripts/knowledge.py --root /home/claude/runs/g1-timer/.claude/skills 2>/dev/null | python3 -c "import json,sys;d=json.load(sys.stdin);print(json.dumps({
$ grep -A15 '^detect' .claude/skills/bmod-method/migration-1.toml .claude/skills/bmod-method/migration-2.toml; git ls-files; cat README.md
$ git status --short && find _bmad -maxdepth 2 | sort
```

</details>

**Reply** (40 s, $0.33):

Hi, I'm the BMad Agent. Setup is finished and the installation is current.

**Installed in project scope:**

| Module | Version | Skills |
|---|---|---|
| core-tools | 6.13.0-next | 11 (bmad, brainstorming, deep-recon, forge-idea, review, party-mode, …) |
| method | 6.13.0-next | 15 (the analyst, PM, PO, architect, UX and dev agents, plus build, code-review, retrospective, …) |

**What setup did:**
- Created `_bmad/` with the shared scripts and a `scripts` folder for each module, `config.toml`, and `.gitignore` files in `_bmad/custom/` and `_bmad/render/`. Personal config answers there stay out of git.
- Neither module asks any config questions, so there were no answers to record or change.
- I found nothing to clean up from v6 and no duplicate or retired skills.
- I didn't run either of the method module's two migrations (v6→v7 and v7 preview→v7). The repo holds only a README, so there's nothing to migrate.

**One thing to know:** I couldn't check for updates. The update source returned 404 for both modules. That's expected for a `-next` pre-release whose files aren't on `main` yet, and it isn't a problem with your install. Once the release is published, `bmad setup` or "update" will pick it up.

> "BMad is ready. You can ask bmad for help or suggestions at any time, and if you add modules or want to check for updates in the future, just ask the bmad agent to update."

`.claude/`, `_bmad/` and `skills-lock.json` aren't tracked by git yet. Commit them when you're ready, since I haven't.

**Where to go next:** for a fresh project like g1-timer, I'd start with `bmad-forge-idea` to stress-test the concept. If you already know what you want, go to `bmad-agent-po` (Sofia) to turn it into an initiative and stories. Tell me what g1-timer should be and I'll take you through it.
