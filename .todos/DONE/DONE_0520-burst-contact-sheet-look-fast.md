# 0520 — Burst review: a contact sheet to check the obvious series at a glance

- **Priority**: High
- **Batch**: review
- **Depends**: —
- **Files**: `src/media_hygiene/review/templates/review_obvious.js.j2`, `src/media_hygiene/review/templates/review.html.j2`, `src/media_hygiene/review/templates/pick_grid.js.j2`, `src/media_hygiene/services/reviewing.py`, `documentation/en/commands/review.md`, `documentation/fr/commands/review.md`

## Asked (maintainer, 2026-10-30)

"I prefer to look, not to accept blindly. Something that reassures me but is fast for a user
with hundreds of thousands of photos." Today the choice is one series at a time (slow) or
*Validate the obvious series* in one write, unseen (blind).

## What — a contact sheet between the two

- A "Contact sheet" view of the obvious series: one compact row per series, the kept shot
  framed in green, the shots proposed aside smaller and dimmed with their reason. As many rows
  as the screen holds (estimated 15–25 on a 1080p screen with 120 px thumbnails).
- **Enter** validates the rows seen on screen and scrolls to the next screen; a click on a shot
  flips it (keep/aside) for its series; a double click opens the large view (shared `pick_*`
  viewer). Z takes back the last screen, whole.
- The doubtful series (non-obvious) stay in the current one-by-one view; the sheet says how many
  are left there.
- Estimated speed: 2–3 s per screen of ~20 series, i.e. ~400 series a minute, each one seen.

Load the `photo-picking-pages` skill first: same keys, same bar, *Apply now* in its place.

## Done when

The contact sheet is the view offered first for the obvious series; *Validate the obvious
series* stays as the fast path, saying in one line that it validates unseen (0524). Tests of
Enter, flip and Z; both languages documented.

## Outcome (2026-11-02)

DONE: a contact sheet of the obvious series (`review_sheet.js.j2`, on the board of
`review_board.js.j2`): 20 compact rows a screen, Enter validates the screen in one write then
the next, a click flips a shot (after 250 ms, so a double click opens the large view instead),
Z takes the screen back whole; the button comes before *Validate … unseen* (V).
