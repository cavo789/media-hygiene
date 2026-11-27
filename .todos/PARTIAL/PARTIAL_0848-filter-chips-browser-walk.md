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

## Status — PARTIAL (2026-11-27)

### Done
- `tests/support/pages_walk.py` `chips_step`: on the search page, 24 words (each one chip, enough to fold into `+N` at Chromium's default 1280 px), then 3, then none; per search it records the chips on the line, in `#chipsFolded`, and whether `+N` shows. `tests/e2e/test_pages_browser.py` asserts line + folded == the words of the last search each time, `+N` shown for 24, hidden for none.

### Not done
- The one-time proof that the step fails on the code before 4e7e6696.
  **Reason:** no browser nor e2e image run in this unattended session (CI's headless walk runs it). Reasoned only: without `chipsFolded.replaceChildren()`, the 3-word search puts the ~20 folded chips of the 24-word one back on the line (`foldChips` appends them), so line + folded is far above 3. To prove it: revert that line locally, run `e2e` (`tests/e2e/test_pages_browser.py`), see the chips assertion fail, restore.
