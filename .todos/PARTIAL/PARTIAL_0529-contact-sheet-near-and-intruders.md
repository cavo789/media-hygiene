# 0529 — Contact sheet for near duplicates and intruders, like bursts

- **Priority**: Medium
- **Batch**: review
- **Depends**: 0520
- **Files**: `src/media_hygiene/review/templates/near_review.js.j2`, `src/media_hygiene/review/intruders_views.py`, `src/media_hygiene/review/templates/`, `documentation/en/commands/review.md`, `documentation/fr/commands/review.md`

## Asked (maintainer, 2026-10-30)

UX brainstorm: the same fast look as 0520 everywhere (same features on every page).

## What

- The contact sheet of 0520 (one compact row per case, the kept file framed, Enter validates
  what is on screen, a click flips, Z takes the screen back) on the near-duplicate page and
  the intruders page, from one shared template rather than three copies.
- Load `photo-picking-pages` first.

## Done when

The three pages use the one sheet template, same keys (test of the keys table).

## Status — PARTIAL (2026-11-03)

- Done: the near-duplicate page has the contact sheet (`near_sheet.js.j2`): the sure groups
  still undecided, one compact row each, the kept version framed; a click on the other version
  keeps it instead (as W), Enter decides the screen in one write (`decideEach`), Z takes it
  back, a double click shows a version large, Esc goes back. The shared parts are one template
  each, used by the bursts and the near duplicates: `sheet_fit.js.j2` (rows a screen, click vs
  double click), `sheet_keys.html.j2` (the keys rows), `contact_sheet.css.j2`;
  `tests/unit/test_contact_sheet.py` checks the same keys on both pages. Checked in headless
  Chromium (mocked API): open, flip, double click, Enter posts one write, no page error.
- Left: the intruders page. It shows no pictures (zips, docx, pdf: "nothing to look at"), so a
  contact sheet of tiles has nothing to show. Needs maintainer: drop that part, or say what a
  row of an intruder case should show (an icon per file?).
- The burst sheet keeps its own rows (`review_board.js.j2`): only its sizing, click and keys
  moved to the shared templates.

## Decided (2026-11-03, review of PR #61)

By the maintainer: the intruders part is dropped (files without a picture: nothing to show on a sheet); in a group of 3+ versions a click keeps the first other version, as built.
