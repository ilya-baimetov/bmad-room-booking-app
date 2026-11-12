# Review: rubric walker (rubric-planning)

Stakes: internal. Altitude: product brief.

## Verdict

The brief is decision-ready, with one clear thesis: one source of truth for rooms that blocks clashes and shows a free room in seconds. It is held back by how much of its body is still tagged guesswork. The argument for standalone over calendar room booking rests entirely on an assumption.

## Three fixes that matter most

1. Move the 12 `[ASSUMPTION]` tags out of the body into one Assumptions list. The user gave a blanket yes, which leaves each tag open.
2. Keep "why standalone" visibly open in that list, so John's PRD confirms or reverses it before anyone builds.
3. Add an open question on moving the bookings already in the spreadsheets at launch. Adoption depends on it.

## Findings by dimension

| Dimension | Rating | Severity | Location | Finding and fix |
|---|---|---|---|---|
| Decision-ready | strong | — | Executive summary | Thesis and trade-off (no-shows deferred) are stated. |
| Earned | strong | — | Throughout | No persona theater or padding. |
| Testable | adequate | low | Success criteria | All four criteria can be checked. "In seconds" is pinned to 10 seconds, but only as an assumption. |
| Honest scope | adequate | medium | What makes it different | Non-goals are clear. The advantage over calendar room booking or a bought product is assumed, not the user's. Keep it open in the Assumptions list. |
| Honest scope | adequate | medium | Scope | Cutover from the spreadsheets (existing future bookings) is not mentioned. Defer as an open question. |
| Usable downstream | strong | — | Throughout | Terms are consistent; no ids to resolve; length fits. |

## Done when

Met. A reader of only the executive summary can say what it is (one booking tool across three offices), who it is for (about 300 staff and office managers) and why now (growth to three offices, return to office).
