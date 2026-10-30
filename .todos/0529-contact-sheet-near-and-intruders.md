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
