# 0848 — Filter chips driven in the CI browser walk

- **Priority**: Low
- **Batch**: library
- **Depends**: none
- **Files**: `tests/support/pages_walk.py`, `src/media_hygiene/search/templates/search_chips.js.j2`

## Why (review of feedback-2026-11-27-iterate)

0820 (commit 4e7e6696) fixed stale chips piling up (+N folded chips coming back), checked only on the rendered script. The maintainer asked for a browser step.

## Do

- In the CI headless walk, set many filters so +N appears, then a search with fewer, then none: the line and the +N panel hold exactly the current chips each time.
- Fails on the code before 4e7e6696 (prove it once).
