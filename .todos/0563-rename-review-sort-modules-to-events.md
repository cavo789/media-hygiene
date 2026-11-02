# 0563 — Rename `review/sort_*.py` to `events_*`

- **Priority**: Low
- **Batch**: search
- **Depends**: —
- **Files**: `src/media_hygiene/review/sort_*.py` (17 modules), their importers and tests

## Why

Review of `feedback-2026-10-29-iterate-3.md` (TODO 0460): `review-sort` is gone, and these modules
now serve the 🗂 Events tab of `search`. The `sort_` prefix misleads a reader (it is not the `sort`
verb).

## What

- `git mv` each `review/sort_*.py` to `review/events_*.py`, update the imports and the test names.
- No behaviour change: `/api/sort/…` routes and `sort-decisions.json` keep their names (files on
  the user's disk).

## Explicit NON-goals

- Renaming routes, JSON keys or the decisions file.
