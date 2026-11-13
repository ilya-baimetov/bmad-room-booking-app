---
name: Room Booking — door screen and check-in states
status: final
ticket: ../initiative-check-in.md
created: 2026-11-13
updated: 2026-11-13
---

# Door screen and check-in states: experience spine

Covers the door tablet's check-in screen (R2, R3, R7), and the check-in and freed states of a booking in My bookings and on its details page (R5). The office manager's tablet setup (R1) and the weekly freed count on Manage rooms (R6) are **not designed here**: the user scoped this run to the two surfaces above. Requirement ids are the initiative's (`../initiative-check-in.md`).

## Foundation

- **Surfaces:** (1) the door screen, a web page of the app shown full screen on an ordinary tablet by each room's door (C2); (2) My bookings and the booking details page, existing pages of the app, gaining check-in states.
- **UI system:** the app's own server-rendered Jinja templates and htmx, with tokens from `roombooker/static/tokens.css`. `DESIGN.md` is the visual reference and names the deltas. Every page works as a full page load, and htmx only narrows the swap with `hx-select` (C5).
- **Who is at the door screen:** anyone walking up. There is no sign-in, no person and no Pick your name. Check-in is anonymous (S11).
- The tablet is roughly 10 inches, in landscape, mounted by the door at standing eye height, and kept awake by its own settings (kiosk mode or never sleep). The app doesn't control the device (C2).

## Information Architecture

| Surface | Reached from | Purpose | Requirement |
|---|---|---|---|
| Door screen | The tablet opens it once set up, and stays on it | Shows the room name, free or booked, the current or next booking, and today's list. Offers one-tap check-in while the window is open. | R2, R3, R7 |
| My bookings (Day, Week) | Top bar tab, as today | Each booking in a room with a tablet carries its check-in state | R5 |
| Booking details | A booking in My bookings or Rooms, as today | Shows the booking's check-in state and hides actions that no longer apply | R5 |

The door screen has no links out: no top bar, no tabs, no "Back". Its only control is Check in, so passers-by can't wander off it into the app.

Not designed here, and needed before the initiative is done: the setup surface (R1), the freed count (R6), and whether a freed booking still appears in the Rooms page's booking list (`bookings/_item.html`).

## Voice and Tone

Plain UK English, 24-hour clock, en dash in time ranges ("10:00–11:00"), and no exclamation marks, matching the existing "Room becomes free for everyone".

| Do | Don't |
|---|---|
| "Free" / "Booked" / "Closed" | "Available" / "Occupied" / "In use" |
| "Check in" | "Claim room", "I'm here", "Start meeting" |
| "Freed at 10:15 if nobody checks in" | "Check in now or lose your room!" |
| "✓ Checked in" | "Check-in successful" |
| "Freed: nobody checked in" (exact, R5) | "No-show", "Released", "Auto-cancelled" |
| "Check in at the door, 09:55–10:15" | "Remember to check in!" |
| "Couldn't check in. Tap Check in again." | "Error 500" |
| "Check-in closed at 10:15" | "Too late" |

## Component Patterns

Behavioural rules. Visual specs are in `DESIGN.md` Components.

| Component | Behaviour |
|---|---|
| Door status panel | Shows the room's state now: **Booked** when a booking is current (started, not ended, not freed), or when the next booking's check-in window has opened. **Free** otherwise. **Closed** when the room is closed. Under the status: the booking it refers to, as title and times. When free: "Next: {title} at 14:00", or "Nothing else today". |
| Check-in countdown | Shown only while a booking's window is open and nobody has checked in: "Freed at {start+15} if nobody checks in". Before the start it reads "Check in from now · Freed at 10:15 if nobody checks in". It is a fixed time, not a ticking timer. |
| Check in button | Present only while a booking's window is open (start − 5 min to start + 15 min) and nobody has checked in. One tap posts a plain HTML form and the page comes back with the panel showing "✓ Checked in". No confirm, no name and no undo (S11). No undo: a mistaken check-in only keeps a booking from being freed, which is the accepted trade-off in the initiative's Notes. |
| Check in button: two bookings | Back to back, if the next booking's window opens while the current booking is still running, the panel stays on the current booking and the button names the one it checks in: "Check in: {next title}, 11:00". It never silently targets a different booking from the one the panel shows. |
| Today's list | Every booking today in this room, in time order: times, title, then a state word: "Checked in", "Freed", "Ended" or nothing for upcoming. Current or next is highlighted. Read close up. Rows aren't tappable. |
| Booking state tag (My bookings, details) | Appears only on bookings in a room with a tablet set up (R7): rooms without one show exactly what they show today. Values: "Check in at the door, 09:55–10:15" for a booking today that hasn't been checked in and whose window hasn't closed; "Checked in"; "Freed: nobody checked in". |
| Details page, freed booking | A "Check-in" row in the details list reads "Freed: nobody checked in. {Room} was freed at 10:15." Cancel booking is hidden. Book again stays. Add to calendar is hidden, since the booking is no longer happening. |
| Details page, checked-in booking | The "Check-in" row reads "Checked in at the door". No time, since nothing else in the app shows when someone acted. |

## State Patterns

Door screen. "Window" means start − 5 min to start + 15 min.

| State | Panel | Below the status | Button |
|---|---|---|---|
| Free, more bookings later | Free (white) | "Next: Design review at 14:00" | none |
| Free, nothing else today | Free | "Nothing else today" | none |
| Next booking's window open, not yet started | Booked (navy) | Title, "10:00–11:00", countdown | Check in |
| Current, window open, not checked in | Booked | Title, times, countdown | Check in |
| Current, checked in | Booked | Title, times, "✓ Checked in" | none |
| Current, window closed without check-in, room has tablet | Freed: Free (white) | "Freed: nobody checked in", "Free until {next booking start}" or "Free for the rest of today" | none |
| Freed slot rebooked by someone else | Booked | The new booking, by its own rules | by its own window |
| Current booking ended | The next state in this table | | |
| Room closed | Closed (grey) | "Closed" | none |
| Tablet not set up, or its setup removed | Plain page, app look | "This tablet isn't set up for a room. Ask your office manager to set it up." | none |
| Tapped Check in after the window closed (race) | Free, freed | Message: "Check-in closed at 10:15. This booking was freed." | none |
| Tapped Check in when someone already had | Booked | "✓ Checked in". The second tap is treated as success, not an error. | none |
| Check-in failed (server or network) | Unchanged | Error message, error red: "Couldn't check in. Tap Check in again." | Check in, kept |
| Lost connection | Last state stays on screen | After 2 minutes without a successful refresh, a small line: "Not up to date. Checking again…" | as last state |

**Staying current.** The door screen refreshes itself every 30 seconds by an htmx poll that swaps the whole page body with `hx-select`, and by a plain meta refresh as the no-JS fallback (C5). The server decides every state from the time of the request. The screen can lag a boundary by up to 30 s. The server still refuses a check-in after start + 15 (the race row above). 30 s is enough.

My bookings and details:

| State | My bookings link | Details "Check-in" row |
|---|---|---|
| Room has no tablet | unchanged | no row |
| Today, window not yet closed, not checked in | navy link + "Check in at the door, 09:55–10:15" | "Check in at the door from 09:55 until 10:15, or the room is freed" |
| Checked in | navy link + "Checked in" | "Checked in at the door" |
| Freed | grey `calendar-booking-freed` + "Freed: nobody checked in" | "Freed: nobody checked in. {Room} was freed at 10:15." |
| Cancelled or removed by room close | gone, as today | n/a |

Attendees see the same states as the organiser. R5 names the organiser, but My bookings also lists bookings someone attends, and an attendee shown a freed booking as still on would walk to a room that's been given away.

## Interaction Primitives

- **Door screen: one tap, nothing else.** No typing, no scrolling at the default zoom, no swipes, no long-press, no gestures.
- The Check in button is a `<form method="post">` with one button. After the post the server redirects back to the door page (post, redirect, get), so a reload never repeats the post. htmx may submit it and swap with `hx-select`, but the plain form must work alone.
- Taps are idempotent: a double tap or two people tapping gives one check-in and both see "✓ Checked in".
- My bookings and details: no new interactions, only new text and the freed fill.
- **Banned on the door screen:** any confirm dialog, any name or code entry, any link out of the page, booking from the tablet (Boundaries), sound, notifications (C1), QR codes (C1).

## Accessibility Floor

Behavioural. Contrast is in `DESIGN.md` (navy on white and white on navy, both well past AA).

- WCAG 2.2 AA on all three surfaces.
- Free and booked are always said in words. Colour only reinforces them.
- The Check in button is at least 96 px tall and spans the panel, reachable from a wheelchair if the tablet is mounted within reach. Setup guidance for office managers should name a mounting height, and belongs with R1.
- After check-in the page's `#announce` live region says "Checked in". Failures are announced the same way.
- No motion, no flashing, no ticking countdown. The only time limit is the check-in window itself, which is the product rule. It is shown as a clock time, never as a timer that counts down.
- Door page has `lang="en-GB"` and a `<title>` of "{Room} · Room Booking".

## Responsive & Platform

| Orientation | Behaviour |
|---|---|
| Landscape (assumed) | Status panel left ~60%, today's list right ~40%. Nothing scrolls. |
| Portrait | Status panel on top, list below. The list scrolls inside itself and the panel stays visible. |
| Phone-sized | Not a target. The page still works, stacked, so anyone opening the door URL in a browser can see it. |

## Key Flows

### Flow 1: Checking in, a few minutes late (Priya, Leeds, Aire, Tuesday 10:07)

1. Priya has booked Aire 10:00–11:00 for "Client review". She's running late from the station, with two colleagues and the client behind her.
2. From the corridor she sees Aire's tablet: a navy panel reading **Aire / Booked / Client review / 10:00–11:00**, and under it "Freed at 10:15 if nobody checks in".
3. She walks up and taps the big **Check in** button without putting her laptop bag down.
4. **Climax:** the page comes back with "✓ Checked in" where the button was, and the countdown is gone. The room is hers until 11:00, and she didn't have to say who she is.
5. Later in My bookings, her 10:00 booking reads "Checked in".

Failure: the tablet lost Wi-Fi. The tap shows "Couldn't check in. Tap Check in again." She taps again once the connection is back, still before 10:15.

### Flow 2: A room nobody came to is freed (Tom, Sam and Deansgate, Manchester, Thursday)

1. Tom booked Deansgate 14:00–15:00 for a one-to-one. The other person cancelled by chat at lunch, and Tom forgot to cancel the room.
2. At 14:00 the tablet shows **Deansgate / Booked / 1:1 / 14:00–15:00**, "Freed at 14:15 if nobody checks in". Nobody comes.
3. At 14:15 (within 30 s) the panel turns white: **Deansgate / Free**, "Freed: nobody checked in", "Free until 15:00". In today's list the 14:00 row reads "Freed".
4. At 14:20 Sam walks past looking for somewhere quiet for a call, and reads "Free until 15:00" from the corridor.
5. **Climax:** Sam books Deansgate 14:20–15:00 on their phone in the app, as for any free time (R4). When the tablet next refreshes it is navy again with Sam's booking. A room that would have sat empty for an hour is in use.
6. When Tom next opens My bookings, the 14:00 booking is grey and reads "Freed: nobody checked in". Its details page says "Deansgate was freed at 14:15" and offers Book again, but not Cancel.

Failure: Tom does turn up, at 14:16. The tablet already shows Free and offers no Check in. His booking was freed. He can book the rest of the slot in the app like anyone else, if Sam hasn't already.

### Flow 3: A room with no tablet (Kingsway, London)

1. Kingsway has no tablet set up yet. Anna, the office manager, hasn't done it.
2. Bookings in Kingsway show no check-in tag in My bookings and are never freed (R7). Nothing about Kingsway changes from today.
