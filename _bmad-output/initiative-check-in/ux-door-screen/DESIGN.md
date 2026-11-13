---
name: Room Booking — door screen and check-in states
description: The door tablet's check-in screen and the check-in states of a booking in My bookings. Extends the app's existing tokens (roombooker/static/tokens.css); only the deltas for reading from a distance and the new booking states are new.
status: final
created: 2026-11-13
updated: 2026-11-13
colors:
  # Inherited unchanged from roombooker/static/tokens.css. No new colors.
  navy: '#1B2A4A'
  navy-hover: '#2A3D66'
  navy-tint: '#E8ECF4'
  white: '#FFFFFF'
  ink: '#1B2A4A'
  ink-muted: '#5B6474'
  border: '#D5DAE3'
  closed: '#F2F3F5'
  error: '#B42318'
  error-tint: '#FDECEA'
typography:
  # title, body, label, meta inherited from tokens.css (system-ui; 20/16/14/14px).
  # New: the door ramp, sized for reading from a few steps away on a ~10in landscape tablet. Check on the real device at 2-3 m before building.
  door-status:
    fontFamily: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif
    fontSize: 88px
    fontWeight: '700'
    lineHeight: '1.0'
  door-room:
    fontFamily: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif
    fontSize: 48px
    fontWeight: '600'
    lineHeight: '1.1'
  door-current:
    fontFamily: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif
    fontSize: 40px
    fontWeight: '600'
    lineHeight: '1.2'
  door-detail:
    fontFamily: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif
    fontSize: 28px
    fontWeight: '400'
    lineHeight: '1.3'
  door-list:
    fontFamily: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif
    fontSize: 24px
    fontWeight: '400'
    lineHeight: '1.3'
rounded:
  sm: 4px
  md: 8px
spacing:
  # 1-6 and touch-target inherited from tokens.css.
  '1': 4px
  '2': 8px
  '3': 12px
  '4': 16px
  '5': 24px
  '6': 32px
  touch-target: 44px
  door-gutter: 32px
  door-check-in-height: 96px
components:
  door-status-panel-booked:
    background: '{colors.navy}'
    foreground: '{colors.white}'
    radius: '{rounded.md}'
  door-status-panel-free:
    background: '{colors.white}'
    foreground: '{colors.navy}'
    border: '{colors.navy}'
    radius: '{rounded.md}'
  door-status-panel-closed:
    background: '{colors.closed}'
    foreground: '{colors.ink-muted}'
    radius: '{rounded.md}'
  door-check-in-button:
    background: '{colors.white}'
    foreground: '{colors.navy}'
    radius: '{rounded.md}'
    min-height: '{spacing.door-check-in-height}'
    typography: '{typography.door-current}'
  door-list-item:
    background: '{colors.white}'
    foreground: '{colors.ink}'
    border: '{colors.border}'
    radius: '{rounded.sm}'
  door-list-item-current:
    background: '{colors.navy-tint}'
    foreground: '{colors.ink}'
    radius: '{rounded.sm}'
  door-list-item-past:
    foreground: '{colors.ink-muted}'
  booking-state-tag:
    background: '{colors.white}'
    foreground: '{colors.navy}'
    radius: '{rounded.sm}'
    typography: '{typography.label}'
  calendar-booking-freed:
    background: '{colors.closed}'
    foreground: '{colors.ink-muted}'
    border: '{colors.border}'
    radius: '{rounded.sm}'
---

## Brand & Style

The door screen is the existing Room Booking app seen from across a corridor. It keeps the app's plain, quiet, navy-and-white look. It adds no new colours, no new typeface and no decoration. The only change is scale. The room name, the word "Free" or "Booked", and the current booking are big enough to read from a few steps away. Everything else on the screen is secondary and can stay small.

The check-in states in My bookings follow the same rule. Each state is a word on the booking, not a new visual language.

## Colors

All colours are inherited from `roombooker/static/tokens.css`. The door screen adds none.

- **Navy (`{colors.navy}`)** fills the status panel when the room is booked. A navy panel or a white one is the cue you can read from furthest away, before any word is legible. Navy keeps its existing meaning: a booking.
- **White (`{colors.white}`)** with a navy border is the status panel when the room is free. It matches the app's existing free slot (`--slot-free-*`).
- **Closed grey (`{colors.closed}`)** is the panel for a closed room and the fill for a freed booking in My bookings. The app already uses grey for out of use, not an error (`app.css`: "grey, never red"). A freed booking is the same kind of thing.
- **Error red (`{colors.error}`)** appears only in a check-in that failed. It is never used for "freed" or for "nobody has checked in yet".

Avoid introducing green for free or amber for pending. "Keep the app's existing look" rules them out. The status word carries the meaning, and the colour reinforces it.

## Typography

Body, label, meta and title are inherited from `tokens.css`. The door screen adds one ramp of five sizes, all in the app's system-ui stack. These values assume a roughly 10-inch tablet at its default zoom. Check them on the real device from 2–3 m before building.

| Role | Token | Used for |
|---|---|---|
| Status | `{typography.door-status}` | "Free", "Booked", "Closed". The largest text on screen. |
| Room | `{typography.door-room}` | The room name, above the status. |
| Current | `{typography.door-current}` | The current or next booking's title, and the Check in label. |
| Detail | `{typography.door-detail}` | Times and the check-in countdown ("Freed at 10:15 if nobody checks in"). |
| List | `{typography.door-list}` | Rows in today's list. Read close up. |

My bookings uses the existing ramp. The state tag uses `{typography.label}`.

## Layout & Spacing

The door screen fills the viewport, with no top bar, no tabs, no person and no scroll at the default zoom. The tablet is in landscape.

- **Landscape:** the status panel takes the left ~60%. It holds the room name, status, current booking and the Check in button. Today's list takes the right ~40%. The outer gutter is `{spacing.door-gutter}`.
- **Portrait:** the status panel is on top, with today's list below it. A long list scrolls inside its own column. The status panel never scrolls off the screen.

My bookings keeps its existing layout and gains only a tag line on each booking.

## Elevation & Depth

None, as in the rest of the app. Panels are flat fills with borders.

## Shapes

Inherited: `{rounded.md}` for panels and the Check in button, `{rounded.sm}` for list rows and tags.

## Components

- **Door status panel.** Three variants: `door-status-panel-booked` (navy fill, white text), `door-status-panel-free` (white fill, navy border and text) and `door-status-panel-closed` (grey). Anatomy, top to bottom:
  1. room name in `door-room`
  2. status word in `door-status`
  3. current booking title in `door-current`, with its times in `door-detail`
  4. the countdown line in `door-detail`, when check-in is open
  5. the Check in button

  When the room is free, line 3 becomes "Next: {title} at 14:00" or "Nothing else today".
- **Door Check in button.** Full width of the status panel and `{spacing.door-check-in-height}` tall, more than twice the app's touch target. On the navy panel it is a white button with navy text. That is the app's secondary button inverted, so it stands out on navy without a new colour. The label is "Check in" in `door-current`. While pressed it shows `{colors.navy-tint}`.
- **Checked-in confirmation.** The button is replaced by the line "✓ Checked in" in `door-current`, white on the navy panel. No button remains.
- **Door list item.** One row per booking today: times, then title, then a state word on the right. Variants: current or next booking uses `door-list-item-current` (navy tint), past bookings use `door-list-item-past` (muted ink), the rest use `door-list-item`.
- **Booking state tag (My bookings, details page).** A small label on a booking: "Check in at the door by 10:15", "Checked in" or "Freed: nobody checked in". On the navy organiser link it is white text with no fill. On a freed booking it is muted ink.
- **Freed booking in My bookings.** `calendar-booking-freed`: grey fill with a border and muted ink, so it reads as no longer happening without looking deleted or like an error. The title stays legible and is not struck through.

## Do's and Don'ts

| Do | Don't |
|---|---|
| Use navy for booked and white for free, so the screen can be read before any word can | Add green, amber or red for room states |
| Use grey for freed: out of use, not a mistake | Use error red for a freed booking or for "not checked in yet" |
| Keep the room name, status and current booking in the door ramp | Put the list or footer text in the door ramp |
| Use one big Check in button | Add a second action, a confirm step or a who-are-you field next to it |
| Show the status word as well as the panel colour | Let colour alone tell free from booked |
