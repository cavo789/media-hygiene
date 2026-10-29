# 0464 — Search: show the files set aside, put them back

- **Priority**: High
- **Batch**: search
- **Depends**: 463
- **Files**: `src/media_hygiene/search/templates/search.html.j2`, `src/media_hygiene/search/templates/search.js.j2`, `src/media_hygiene/search/chosen.py`, `src/media_hygiene/search/chosen_api.py`

## Why

The maintainer, 2026-10-29: no way to see what was set aside before it goes to quarantine.

## What

The counter *🗑 N set aside* is clickable and *Show* gets a 4th segment *🗑 set aside*: the same
grid lists those files (from the decisions file the counter already reads, no new data), with a
filter chip to leave. On them, *put back* (one or a selection) undoes the set-aside; the save is
read back from disk before the counter changes.

## Acceptance

- Set 3 aside, view them, put 1 back: the file on disk lists 2, the counter says 2. Grid does not jump.
