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

## Status (2026-10-29): DONE

`classify/event_title.py`: « {activity} in {place} » (« Promenade à Liège »), else
« Liège — 29 octobre », else the day; the activity from a small EN+FR word list over the
vision tags, named when at least half the described photos share it (`SHARED`, a constant).
`search/event_suggest.py` reads the `place` (personal first, else town) and `vision` tags of an
event's photos; the 🗂 Events card shows *💡 Proposed name: … [Use this name]*: one click
fills the name and saves it (read back as every choice); nothing is sorted. Used too by the
end of the phone import (0475). Tests: `tests/unit/test_event_title.py`. Docs EN+FR (search).

Not measured: the share of names kept as proposed (demo tree has no vision tags; needs the
maintainer's real import — step 39e of `mh-measure.ps1` records the name proposed).
