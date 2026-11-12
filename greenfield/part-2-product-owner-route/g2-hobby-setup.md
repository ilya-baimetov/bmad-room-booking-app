# Set up BMad (`/bmad setup`)

Label `g2-hobby-setup`. 
1 turns, 0 min 37 s wall time, $0.27. Session: [`f3baa27c`](raw/f3baa27c-113f-409a-b0c6-12a3ab3413b5.jsonl).


## Turn 1

**You typed:**

````text
/bmad setup
````

<details><summary>What the agent did (7 tool calls)</summary>

```text
Read /home/claude/runs/g2-hobby/.claude/skills/bmad/references/setup.md
$ which uv; ls -a; ls .claude/skills | head -50; uv run --no-cache .claude/skills/bmad/scripts/setup.py --project-root /home/claude/runs/g2-hobby --skill /home/claude/runs/g2-hobby/.
$ uv run --no-cache .claude/skills/bmad/scripts/setup.py --project-root /home/claude/runs/g2-hobby --skill /home/claude/runs/g2-hobby/.claude/skills/bmad --root /home/claude/runs/g2-
$ uv run --no-cache .claude/skills/bmad/scripts/setup.py --project-root /home/claude/runs/g2-hobby --skill /home/claude/runs/g2-hobby/.claude/skills/bmad --root /home/claude/runs/g2-
Read /home/claude/runs/g2-hobby/.claude/skills/bmad/references/migrate.md
$ uv run .claude/skills/bmad/scripts/knowledge.py --root /home/claude/runs/g2-hobby/.claude/skills 2>/dev/null | python3 -c "import json,sys;d=json.load(sys.stdin);print(json.dumps({
$ grep -A15 '^detect' .claude/skills/bmod-method/migration-1.toml .claude/skills/bmod-method/migration-2.toml; ls -R _bmad | head -40; cat README.md | head -20
```

</details>

**Reply** (37 s, $0.27):

Hi Ilya, I'm the BMad Agent. Setup is finished and the installation is now **current**.

**What I did**
- This was a first install, so I created `_bmad/` with `config.toml`, the shared scripts, each module's scripts, and a `custom/` folder that has a `.gitignore` to keep personal answers out of commits.
- No config questions came up, so nothing was asked and no answers were written. Defaults apply.

**Installed modules** (both project scope)
| Module | Version | Skills |
|---|---|---|
| core-tools | 6.13.0-next | 11 (bmad, brainstorming, deep-recon, forge-idea, review, party-mode, …) |
| method | 6.13.0-next | 15 (the analyst, PM, PO, architect, UX and dev agents, plus build, code-review, retrospective, …) |

**Checks**
- **Updates:** I couldn't check for them. Both modules point to sources upstream that return 404 (`main/skills/*/bmod.toml`). This build is a `-next` pre-release, so the files may only exist on another branch. It isn't a fault in your install, but `npx skills update` won't find anything until that changes.
- **v6 leftovers:** none.
- **Migrations:** `method` ships two (v6 → v7 and 7-preview → 7). Neither applies, because this repo has no planning or ticket artifacts yet.
- No duplicates, retired skills, unmet requirements or other problems.

The module's post-install message:
> "BMad is ready. You can ask bmad for help or suggestions at any time, and if you add modules or want to check for updates in the future, just ask the bmad agent to update."

`_bmad/`, `.claude/` and `skills-lock.json` are untracked in git, so commit them when you're ready. The repo has nothing in it but a README. If you're starting a new hobby project, I'd begin with `bmad-forge-idea` to pressure-test the idea, or ask me "what's next" and I'll walk you through it.
