# 0597 — `classify` and `sort` honour the day of a sidecar

- **Priority**: Medium
- **Batch**: search
- **Depends**: 0531
- **Files**: `src/media_hygiene/services/xmp_towns.py`, `src/media_hygiene/classify/dates.py`, `src/media_hygiene/search/move_go.py`, `src/media_hygiene/search/sidecar_days.py`

## Why

0531 writes a day into `.xmp` sidecars and `search` reads it back, but `classify`, `sort` and
*Move to an event…* still read only the index's `media_date`: a photo dated on the page has no
month for them. Seen while closing 0531.

## What

- A file without a date of its own takes its sidecar's day in the classify inputs and in the move
  (`search.sidecar_days.days_of`: only the undated files' folders are listed).
- A test: dated on the page, *Move to an event…* files it in that month; undone: no month again.
- Documentation en + fr: drop the line "the day counts in `search` only".
