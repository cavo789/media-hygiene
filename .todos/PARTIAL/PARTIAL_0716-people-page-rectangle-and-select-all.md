# 0716 — People page: rectangle selection and Ctrl+A over faces

- **Priority**: Medium
- **Batch**: people
- **Depends**: 0712
- **Files**: `src/media_hygiene/people/templates/people_sections.js.j2`, `src/media_hygiene/people/templates/people_name_face.js.j2`, `src/media_hygiene/review/templates/pick_*`

Follow-up of 0712 (PARTIAL): the people page picks faces with ✎, Ctrl and Shift click,
but not by dragging a rectangle nor Ctrl+A / invert, and does not use the shared
`pick_grid.js` behaviour (skill `photo-picking-pages`: a page that differs is a bug).

## Proposal

- Move the face picking of the people page onto the shared `pick_*` gestures (rectangle,
  Ctrl+A, invert, same keys), scoped to one section.
- "These N faces are… [name]" acts on the visible picked faces only, count stated.

## Tests

- Rectangle and Ctrl+A pick the faces of one section only; hidden faces untouched.
- Check the gestures in Chromium (skill checklist step 2).

## Status — PARTIAL (2026-11-12)

### Done

- Rectangle dragged over a section picks the faces it touches, that section only (Ctrl keeps
  those picked); Ctrl+A picks every face the current section shows (never in a field, never
  in the large view). `people/templates/people_face_band.js.j2`; faces carry `data-key`.
- "These N faces are… [name]" unchanged: it acts on the faces picked, count stated.
- Checked in headless Chromium (playwright image, page rendered by the app, API mocked):
  rectangle over 2 faces picks 2 and opens no large view, Ctrl+A picks 4 of section 1 and 0
  of section 2, no `pageerror`.

### Not done

- Invert (`I`): the people page's `i` already ignores a group (since 0667); giving `I` the
  grid's meaning would change a key users know. Needs the maintainer's choice (another key,
  a button in the namer line, or move *ignore the group*).
- The shared `pick_band.js.j2` is bound to the grid's state (`picked`, `files`, `cards`):
  the people page has its own rectangle on the same rules. Making `pick_band` generic (a
  callback for the cards and the pick) would let both share one script.
