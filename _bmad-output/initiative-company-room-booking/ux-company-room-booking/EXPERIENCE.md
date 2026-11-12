---
name: Company Room Booking
status: final
created: "2026-11-12"
updated: "2026-11-12"
sources:
  - ../brief-company-room-booking/brief-company-room-booking.md
  - ../prd-company-room-booking/prd-company-room-booking.md
---

# Company Room Booking: Experience Spine

## Foundation

Responsive web app, one surface used on laptops and phones. No UI kit named: plain HTML and CSS served by the app [ASSUMPTION: the architecture decides how pages are rendered]. `DESIGN.md` is the visual identity reference; this spine is the experience.

Release one has no login (PRD RULE-6). A person picks their name once, and the app remembers it on that device (PRD FR-2, A2). The current person's name is always visible in the top bar. English only, no dark mode, UK time with 24-hour clock [ASSUMPTION].

## Information Architecture

| Surface | Reached from | Purpose | PRD |
|---|---|---|---|
| Pick your name | First visit on a device; top bar name | Choose who you are from the loaded people | FR-1, FR-2 |
| Rooms (main screen) | App open; "Rooms" tab | Today's rooms in my office, free and booked. Laptop: day grid. Phone: next free rooms as a list | FR-6 |
| Booking sheet | Tapping a free slot or a room row's "Book" | Make a booking in three taps or fewer | FR-7, FR-8 |
| Booking details | Tapping any booking (grid, list, calendar) | See title and organiser; change or cancel when allowed | FR-9, FR-10, FR-11, FR-13 |
| My bookings | "My bookings" tab | My own calendar, by day and by week | FR-12, FR-14 |
| Manage rooms | "Manage rooms" tab, office managers only | Add, edit, close and reopen my office's rooms | FR-3, FR-4, FR-5 |

Navigation: tabs in the top bar (Rooms · My bookings · Manage rooms). "Manage rooms" appears only for office managers. Sheets and panels stack one level deep, never two.

Closure: every PRD capability FR-1 to FR-14 has a surface, and every surface is reached by a Key Flow below.

## Booking Visibility

Settles PRD OQ-2 (user): **anyone can see a booking's title and who booked it.** It's an internal tool.

| Detail | Who sees it |
|---|---|
| Room is taken, time, title, organiser | Everyone |
| Attendees | The organiser, the attendees, and office managers of the room's office |

## Voice and Tone

Microcopy. Brand posture lives in `DESIGN.md`.

| Do | Don't |
|---|---|
| "Booked. Atlas, 14:00–14:30." | "Your booking was created successfully!" |
| "Someone just booked Atlas at 14:00. These rooms are still free:" | "Error 409: conflict" |
| "Free until 15:30" | "Available for the next 90 minutes" |
| "Closed" | "Unavailable (room status: inactive)" |
| "No bookings this week." | "Looks like you have nothing planned! 🎉" |
| Times as 14:00, dates as "Tue 17 Nov" [ASSUMPTION] | 2pm, 11/17 |

Short, plain, no exclamation marks. Name the room and the time in every confirmation.

## Component Patterns

Behavioral. Visual specs live in `DESIGN.md.Components`.

| Component | Use | Behavioral rules |
|---|---|---|
| Name picker | Pick your name | Type-ahead search over all ~300 people; shows name and home office. Picking sets the current person on this device and opens Rooms. |
| Office switcher | Rooms | Defaults to my home office. Switching shows that office's rooms; the choice lasts for the visit, then resets to home [ASSUMPTION]. |
| Date switcher | Rooms, My bookings | Today by default; previous/next day; "Today" button returns. |
| Day grid | Rooms, laptop | One row per room, time across in 15-minute columns from 07:00 to 20:00. Tapping a free slot opens the booking sheet with that room and start time. Tapping a booked slot opens booking details. |
| Next free rooms list | Rooms, phone | Rooms in my office free from the next quarter-hour, each with "Free until …" and a "Book" button; free-now rooms first, then by soonest free [ASSUMPTION]. Rooms already taken for the next hour sit below a "Busy now" heading; closed rooms are hidden from the list [ASSUMPTION]. A length choice (30 min / 1 h / 2 h) filters to rooms free for that long [ASSUMPTION]. |
| Booking sheet | From a slot or room row | Room, start time and length prefilled (length defaults to 30 minutes). Title prefilled as "{Name}'s meeting" and editable, so booking needs no typing. Attendees optional, picked by type-ahead. Length: 15 min to 4 h in 15-minute steps (PRD RULE-2). "Book" is the only primary action. |
| Booking details | From any booking | Shows room, time, title, organiser (attendees per Booking Visibility). "Change" and "Cancel booking" appear only when PRD RULE-3 allows: organiser, or an office manager of the room's office. "Cancel booking" asks once for confirmation [ASSUMPTION]. |
| My bookings calendar | My bookings | Day and week toggle. Shows bookings I organise and bookings I attend (PRD FR-12, A4), each marked "Organiser" or "Attending". Previous/next day or week. |
| Rooms table | Manage rooms | My office's rooms: name, capacity, status (Open/Closed). "Add room", and per row "Edit" and "Close" / "Reopen". Closing asks for confirmation and says how many future bookings the room has; what happens to them is decided in the epic (PRD FR-5). |

## State Patterns

| State | Surface | Treatment |
|---|---|---|
| No name picked on this device | Any | Open Pick your name first; return to the requested surface after. |
| Slot taken a moment earlier | Booking sheet | Booking refused (PRD FR-8). Error message above "Book": "Someone just booked {room} at {time}. These rooms are still free:" with up to three free rooms for the same time, each one tap to book. The sheet keeps title and attendees. |
| Change would overlap | Booking details | Same refusal message; the original booking is unchanged. |
| Room closed | Day grid | Row in closed style with "Closed"; no slots tappable. Hidden from the phone list. |
| Past times | Day grid | Slots before now are greyed and not tappable [ASSUMPTION]. |
| No free rooms | Phone list | "No rooms free in {office} for {length} from {time}." Offer the next time any room is free, and the office switcher. |
| Empty calendar | My bookings | "No bookings today." / "No bookings this week." |
| Not an office manager | Manage rooms | Tab hidden; a direct link shows "Only office managers can manage rooms." |
| Save failed (network) | Any form | Error message: "Couldn't save. Check your connection and try again." Form keeps its values. |
| Loading | Rooms, My bookings | Grid or list outline appears at once; content fills in. Free rooms within the 10-second target (PRD RULE-8). |

## Interaction Primitives

- **Tap or click** to act. No drag, no swipe gestures, no long-press in release one [ASSUMPTION].
- **Three taps or fewer to book (user):** laptop: tap a free slot → "Book" (2 taps). Phone: "Book" on a room row → "Book" (2 taps). Changing length, title or attendees is optional and adds taps only when wanted.
- **Times snap to 15 minutes** in every picker (PRD RULE-2).
- **Keyboard:** Tab moves through controls in reading order; Enter activates; Esc closes the booking sheet or details panel.
- **Banned:** sheets on top of sheets; hover-only actions; confirmation dialogs for booking (refusal handles conflicts); auto-refreshing the grid under the user's finger.

## Accessibility Floor

Behavioral. Visual contrast lives in `DESIGN.md` (white on navy and ink-muted on white both meet AA).

- WCAG 2.2 AA across laptop and phone [ASSUMPTION].
- Slot and room state is always in words ("Free", "Booked: {title}, {organiser}", "Closed"), never color alone.
- The day grid is a real table: room names as row headers, times as column headers, so screen readers announce "Atlas, 14:00, Free".
- Every tap target is at least 44px.
- Booking results and refusals are announced through a live region.
- Focus moves into the booking sheet when it opens and back to the tapped slot or row when it closes.

## Responsive & Platform

| Width | Rooms | My bookings | Booking sheet |
|---|---|---|---|
| ≥ 768px (laptop) | Day grid, all rooms visible | Week grid or day column | Centred panel |
| < 768px (phone) | Next free rooms list, not a calendar (user) | Day list by default; week as seven day-headed lists [ASSUMPTION] | Bottom sheet |

Tabs stay in the top bar at every width [ASSUMPTION]. Manage rooms works on phone as a simple list, but is designed laptop-first [ASSUMPTION].

## Key Flows

Journey names mirror the PRD. Protagonists are roles, because no real session was narrated [ASSUMPTION, PRD A1].

### UJ-1: A Leeds staff member books a room for this afternoon

1. Opens the app on their phone. It remembers their name, so Rooms opens on Leeds, today.
2. The next free rooms list shows rooms free from 14:00. They choose "1 h".
3. They tap "Book" on a room showing "Free until 16:00".
4. The booking sheet opens with room, 14:00–15:00 and "{Name}'s meeting" filled in. They add two colleagues as attendees.
5. **Climax:** they tap "Book". "Booked. {Room}, 14:00–15:00." The booking appears in their My bookings and in both attendees' calendars. Two taps, plus the attendees they chose to add.

Failure: someone booked that room a moment earlier. The sheet shows the refusal and three rooms still free at 14:00; one tap books another.

### UJ-2: A Manchester staff member books a room in London for a visit

1. On their laptop, Rooms opens on Manchester. They switch the office to London and the date to next Tuesday.
2. The day grid shows London's rooms; they tap a free slot at 10:00.
3. In the sheet they set the length to 2 h and add London colleagues.
4. **Climax:** "Book". The slot turns solid navy, with their title on it, in London's grid.

### UJ-3: An organiser moves and cancels meetings

1. They open My bookings, week view.
2. They tap a meeting; details show "Change" and "Cancel booking".
3. "Change": they move it to Thursday 11:00; the app checks the room is free and saves.
4. They open another meeting and tap "Cancel booking", then confirm.
5. **Climax:** the week view updates at once; the cancelled room shows as free in Rooms for everyone.

### UJ-4: A London office manager closes a room for repairs

1. They open Manage rooms; the table lists London's rooms.
2. "Close" on a room: the confirmation says it has 3 future bookings and that closing stops new bookings.
3. They confirm; the room shows "Closed" in the grid. Later they "Add room" for a newly fitted room.
4. From the Rooms grid they tap someone's booking in a London room; as an office manager they see "Change" and "Cancel booking" and move it to free the slot for an urgent meeting.
5. **Climax:** the grid shows the closed room greyed out, the new room open, and the urgent slot free. The room list matches reality.

## Open items

- What happens to future bookings when a room closes is decided in the rooms epic (PRD FR-5); the UX only shows the count.
- Exact company navy and any logo: to be supplied; DESIGN.md hex values stand until then.
