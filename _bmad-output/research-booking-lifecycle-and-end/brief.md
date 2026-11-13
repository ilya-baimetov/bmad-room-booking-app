# Brief

Commit: 9184f9df73e5814b9fa6eeded775adb5722ab308 (short 9184f9d)
File budget per question: 15
History budget per question: 10
Validation: normal

Excluded from every search (relative to the repository): `_bmad-output/`, `_bmad/`, `.claude/`

## Questions

1. (how) How does a booking stop being active today? What marks its end (end time, cancellation, deletion, anything else), and which code paths and database triggers produce each one?
2. (what touches) What reads a booking's end time, or depends on a booking existing or being removed? This covers listings, calendar views, the iCal download and feed, overlap checks, room closing, and seed/demo data.
3. (how) How do the overlap triggers (`migrations/versions/0003_bookings.py`) and the trigger `rooms_close_cancels_future_bookings` decide which bookings count, for example past vs future and current vs removed?
4. (why) Why is the end of a booking represented the way it is, for example as a delete rather than a recorded state?
5. (how) How are a booking's lifecycle, its end, and its removal tested?
