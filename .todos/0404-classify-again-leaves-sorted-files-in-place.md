# 0404 — classify again leaves every sorted file in place, however it got there (tests)

- **Priority**: High
- **Batch**: sort
- **Depends**: 0401, 0402, 0403
- **Files**: `tests/integration/test_classify_stable.py`, `src/media_hygiene/classify/folders.py`, `src/media_hygiene/classify/event_folders.py`, `src/media_hygiene/classify/engine.py`

## Why

The maintainer's second fear (2026-10-25): "if I run `mh classify` again, what was done
by rules, or by a move from the search page, stays as we planned". With the convention
of 0401 the promise is simple: **a file in `YYYY/YYYY-MM/<name>` (or directly in
`YYYY/YYYY-MM`) is in place**. `existing_folder` reads the name, the layout renders the
same path, nothing to move. It must be **proven**, one test per way a file arrives, not
assumed. Today the old layout `{year}/{category}` would propose again a folder sorted
by hand into `2009/2009-11/…` (read in the user's `config.toml`, 2026-10-25).

## What to do

An integration test module on a small synthetic tree (real files, never real photos),
each case: arrange, `classify`, assert **no row to move** for those files (`in_place` or
stay) and the progress counts (0405) unchanged:

1. Sorted by a rule (`sort` of the whole plan), then `classify` again.
2. Sorted by `sort --event` / `review-sort`'s *Sort this event now*.
3. Moved from the search page (0403), with no rule saved.
4. Moved by hand into `2009/2009-11/Name` (Explorer), never seen by the tool.
5. The event folder renamed by hand (`Name` → `Other name`): stays under its new name.
6. A file directly in `2009/2009-11` (nothing special): stays, even when an event of
   that month has a named folder (0402 §3).
7. A stage kept below the event (`2019/2019-07/Montenegro/Budva`).
8. A date rule written **after** the files were sorted, covering those days: the files
   in another named folder do not move (the rule takes no file of a folder the user named
   with another meaning; decide here whether that is a rule of the engine or only of the
   page of 0403, and test it).

Fix in `src/` whatever a case shows (expected: `folders.py` for `YYYY-MM`,
`event_folders.py`, the ordering of `existing_folder` against date rules).

## Tests

This TODO is the tests; `tests_for.py --depth 1` on whatever `src/` file changes.

## Decided (maintainer, 2026-10-25): case 8 lives in the engine

A date rule (`date_range`, `calendar`) takes **no file of a folder named with another
meaning**, in `classify` itself (so `review-sort`, `search` and `sort` all follow). "Another
meaning" is decided **by dates** (0403): a meaningful folder whose files form one event;
a folder spanning several events or months is a batch the rule may take from.
