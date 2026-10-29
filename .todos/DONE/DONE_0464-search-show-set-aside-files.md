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

## Done (2026-10-29)

- **Show** has a 4th segment 🗑 (the files set aside only); the bar's *🗑 N set aside* counter
  opens it; ✕ next to it (always there, greyed outside this view) leaves it. Never remembered
  for the next visit.
- Server: `SearchAsked.aside` narrows the search to the decisions file's paths
  (`Filters.only`, `json_each`), for the list and for *Pick all N found*; no new data.
- *Take out of the set aside* (existing button, one or a selection) puts them back; the
  answer is read back from disk, the tiles stay in place (relabelled).
- Test: `test_show_set_aside_lists_them_and_put_back_is_read_from_disk` (3 aside → listed →
  1 put back: file on disk 2, counter 2, list 2).
- Not done: headless Chromium check of the grid's top; `docs_screenshots` should run.
