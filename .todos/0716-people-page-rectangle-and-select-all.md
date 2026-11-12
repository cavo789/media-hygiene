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
