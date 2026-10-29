# 0477 — Name the new photos' events automatically (place + activity), confirmed in one click

- **Priority**: Medium
- **Batch**: phone
- **Depends**: 0472
- **Files**: `src/media_hygiene/classify/`, `src/media_hygiene/review/sort_*.py`, `src/media_hygiene/search/templates/search_events.js.j2`

## Why

The maintainer, 2026-10-29: after an import the slideshow should tell « Promenade à Liège »
without the user typing it (0475, step 5).

## What

- Group the new photos by day and place (as `classify` does), then propose a name:
  1. always: place + date (« Liège — 29 octobre »);
  2. better: + the activity from the tags most of the group shares (« promenade », « anniversaire »,
     « plage ») → « Promenade à Liège » (a small list of activity words per language; no AI call
     beyond the tags already there).
- The name is a **proposal** in search's 🗂 Events tab, confirmed or changed in one click: nothing
  is sorted without the user (the `sort` rule).
- Measure on the demo tree and, by the maintainer, on a real import: share of names kept as proposed.

## Acceptance

- Unit tests: a group with GPS + shared tag → « Promenade à Liège »; no tag → « Liège — 29 octobre »; no GPS → the date only.
