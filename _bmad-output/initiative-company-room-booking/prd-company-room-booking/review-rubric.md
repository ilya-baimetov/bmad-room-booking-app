# Review: rubric walker (rubric-planning)

Stakes: internal. Altitude: initiative.

## Verdict

A capability-first initiative PRD with a clear thesis, clean ids and explicit non-goals; Sofia can lift it into Requirements and Constraints as written. Its weakness is that 17 assumptions remain unconfirmed, including two that shape features (FR-12 attending, RULE-2 steps), so the done-when line "the user remembers making every decision" does not fully hold.

## Three fixes that matter most

1. Gather the 17 unconfirmed tags into one Assumptions list so downstream readers see what still rests on a guess.
2. Add a non-goal for notifications: nothing says whether attendees are told about a booking, so an epic could invent email.
3. Keep OQ-2 (who sees booking details) visibly owned and needed by UX; it decides what every screen shows.

## Findings by dimension

| Dimension | Rating | Severity | Location | Finding and fix |
|---|---|---|---|---|
| Decision-ready | strong | — | Vision, Decisions | Thesis and trade-offs (no login, standalone) stated with alternatives beaten. |
| Earned | adequate | low | Users and journeys | Journeys are drafted, not narrated, and tagged as such. Acceptable for an internal capability-first tool. |
| Testable | strong | — | FR-1..14 | Each FR has one checkable result at initiative altitude. |
| Honest scope | adequate | medium | Non-goals | No line on notifications (email, push). Add as an unconfirmed non-goal. |
| Honest scope | adequate | medium | Throughout | 17 assumptions open after a skipped walkthrough. Gather into an Assumptions list. |
| Usable downstream | strong | — | ids | check_ids clean; glossary nouns used consistently; 2,224 words, under the 3,000 ceiling. |

## Done when

- Every FR checkable and traced to a journey: met.
- Non-goals and out-of-scope explicit: met, with notifications missing.
- Counter-metric named: met (SM-5).
- Shape fits the product: met (capability spec with short journeys).
- User remembers every decision, nothing invented: partly. The assumptions are tagged, not hidden, but they are unconfirmed.
