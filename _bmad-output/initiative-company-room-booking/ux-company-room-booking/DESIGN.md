---
name: Company Room Booking
description: Internal room booking for London, Manchester and Leeds. Company navy and white; plain, fast, tool-like.
status: final
created: "2026-11-12"
updated: "2026-11-12"
colors:
  # Company colors are navy and white (user). The navy hex is a placeholder until the company's exact value is supplied (user).
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
  # No company font named: system font stack. [ASSUMPTION]
  title:
    fontFamily: 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif'
    fontSize: 20px
    fontWeight: '600'
    lineHeight: '1.3'
  body:
    fontFamily: 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif'
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.5'
  label:
    fontFamily: 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif'
    fontSize: 14px
    fontWeight: '600'
    lineHeight: '1.4'
  meta:
    fontFamily: 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif'
    fontSize: 14px
    fontWeight: '400'
    lineHeight: '1.4'
rounded:
  sm: 4px
  md: 8px
spacing:
  '1': 4px
  '2': 8px
  '3': 12px
  '4': 16px
  '5': 24px
  '6': 32px
  touch-target: 44px
components:
  top-bar:
    background: '{colors.navy}'
    foreground: '{colors.white}'
  button-primary:
    background: '{colors.navy}'
    foreground: '{colors.white}'
    hover: '{colors.navy-hover}'
    radius: '{rounded.md}'
    minHeight: '{spacing.touch-target}'
  button-secondary:
    background: '{colors.white}'
    foreground: '{colors.navy}'
    border: '{colors.navy}'
    radius: '{rounded.md}'
    minHeight: '{spacing.touch-target}'
  slot-free:
    background: '{colors.white}'
    foreground: '{colors.ink-muted}'
    border: '{colors.border}'
  slot-booked:
    background: '{colors.navy-tint}'
    foreground: '{colors.ink}'
    radius: '{rounded.sm}'
  slot-mine:
    background: '{colors.navy}'
    foreground: '{colors.white}'
    radius: '{rounded.sm}'
  slot-closed:
    background: '{colors.closed}'
    foreground: '{colors.ink-muted}'
  room-row:
    background: '{colors.white}'
    border: '{colors.border}'
    radius: '{rounded.md}'
    minHeight: '{spacing.touch-target}'
  booking-sheet:
    background: '{colors.white}'
    radius: '{rounded.md}'
  error-message:
    background: '{colors.error-tint}'
    foreground: '{colors.error}'
    radius: '{rounded.sm}'
---

## Brand & Style

Company Room Booking is an internal tool, and it should look like one: the company's navy and white, plain surfaces, nothing decorative. Its whole job is to show, at a glance, which rooms are free and to get a person into one in three taps or fewer. The visual language serves that glance: white means free, navy means taken, and nothing else on the screen competes with those two. [ASSUMPTION: the posture "plain and tool-like" is inferred from "internal tool" and the company colors.]

## Colors

Two company colors, navy and white (user), and a small set of supporting tones. The navy hex is a placeholder until the company's exact navy is supplied; the supporting tones follow from it.

- **Navy (`#1B2A4A`)** is the company color. Used for the top bar, primary buttons, the user's own bookings, and body text. Navy means "this is ours / act here".
- **White (`#FFFFFF`)** is the canvas and the color of a free slot. Free space is literally empty space.
- **Navy tint (`#E8ECF4`)** marks a slot booked by someone else: taken, but not yours.
- **Ink muted (`#5B6474`)** for secondary text: times, capacities, "free until" labels.
- **Border (`#D5DAE3`)** for grid lines, row outlines and input borders.
- **Closed (`#F2F3F5`)** for a closed room's row: visibly out of use, not an error.
- **Error (`#B42318`, on `#FDECEA`)** only for a refused booking or a failed save. [ASSUMPTION: an error red is added because refusals must stand out; it is the only non-navy hue.]

Avoid: any other brand hue, gradients, or using color alone to mean free, booked or closed (each always carries a text label; see EXPERIENCE.md Accessibility Floor).

## Typography

System font stack throughout [ASSUMPTION: no company font named]. Four roles: `title` (20px, screen headings), `body` (16px, default text and inputs; 16px also stops phones zooming into fields), `label` (14px semibold, room names, buttons, column heads), `meta` (14px, times and secondary detail). Nothing smaller than 14px.

## Layout & Spacing

A 4-based spacing scale (`{spacing.1}` to `{spacing.6}`). Every tappable element is at least `{spacing.touch-target}` (44px) tall.

- **Laptop (768px and wider):** full-width day grid, rooms as rows and time as columns, so all 10–15 rooms of an office fit on one screen without scrolling vertically.
- **Phone (under 768px):** a single column of room rows, `{spacing.4}` side margins.

Breakpoint behavior is in EXPERIENCE.md Responsive & Platform.

## Elevation & Depth

Flat. The only raised element is the booking sheet (a light shadow over a dimmed page). No shadows as decoration.

## Shapes

`{rounded.sm}` (4px) for slots in the grid and error messages; `{rounded.md}` (8px) for buttons, room rows and the booking sheet. No pills or circles. Focus rings follow each element's own shape.

## Components

- **Top bar:** `{colors.navy}` with white text: app name, the current person's name (tap to switch), and the navigation tabs.
- **Primary button:** navy fill, white text, `{rounded.md}`, at least 44px tall. One per screen or sheet: "Book", "Save", "Add room".
- **Secondary button:** white with a navy outline: "Cancel booking", "Close room", "Change".
- **Day grid slot:** four looks, each with a text label as well as color. *Free*: white with a hairline border. *Booked by someone else*: navy tint, showing title and organiser. *Mine* (I organise or attend): solid navy, white text. *Closed room*: grey row with the word "Closed".
- **Room row (phone):** white card with border: room name and capacity on the left; "Free until 15:30" in `meta`; a "Book" button on the right.
- **Booking sheet:** a white panel over the page: bottom sheet on phone, centred panel on laptop. Room, time and length prefilled; title and attendees editable; one primary "Book" button.
- **Error message:** error text on error tint, directly above the button it relates to.

## Do's and Don'ts

| Do | Don't |
|---|---|
| Keep to navy, white and the listed supporting tones | Add a second brand color or decorative accents |
| Label every slot state in words as well as color | Rely on navy vs. white alone to say "booked" |
| Make every tap target at least 44px | Shrink rows to fit more on a phone |
| Use error red only for refusals and failed saves | Use red for closed rooms or past times |
| Keep the grid flat and dense on laptop | Add cards, shadows or icons to grid cells |
