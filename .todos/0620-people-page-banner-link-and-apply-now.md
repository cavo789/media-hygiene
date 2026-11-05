# 0620 — Faces page: the Apply all banner leads to it, and it offers Apply now

- **Priority**: Medium
- **Batch**: people
- **Depends**: 0587 (DONE), 0600 (DONE)
- **Files**: `src/media_hygiene/cli/home_pending.py`, `src/media_hygiene/people/`, `src/media_hygiene/review/`

## Why

Review of 0587/0600: the home server now serves `/people/` once faces are found; the banner names faces set aside but cannot link there, and the page has no *Apply now*.

## What

The banner links to `/people/` when the home server serves it; the page offers *Apply now* (`ApplyOffer`, shared template, same place in the bar) once something is pending (product rule).

## Done when

Banner link and Apply now on `/people/` (tests, headless Chromium).
