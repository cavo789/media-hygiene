# 0800 — Events: try one month

- **Priority**: Medium
- **Batch**: one-interface
- **Depends**: —
- **Files**: `tests/e2e/test_sort_trial_browser.py`, `tests/support/trial_walk.py`

Follows PARTIAL 0745 (`.todos/PARTIAL/PARTIAL_0745-left-by-0526-sort-trial-on-a-sample.md`); decided by the maintainer in the review of 2026-11-13 (`.claude/plans/feedback-2026-11-13-iterate.md`).

A *Try on one month* button on library's 🗂 Events tab: the sort runs on one month first, shown, with *Apply now* (`ApplyOffer`) for what it set; proven in Chromium (a browser test reads the result back).

## Status — DONE (2026-11-13)

- The button already existed (0640, survives a reload since 0648): *Try on one month* on
  the Events tab, the month sorted, its photos shown at their new folders, ↶ Undo, *Sort the
  rest*. Checked in the code; nothing to add on the page.
- *Apply now*: the trial moves files at once (journaled, ↶ Undo); it sets nothing aside, so
  nothing is pending for `clean --decisions`. The library page already carries the shared
  `apply_now` offer for what is set aside there.
- Chromium proof: `tests/e2e/test_sort_trial_browser.py` runs the trial for real through the
  library app (files moved on disk, read back), then `tests/support/trial_walk.py` clicks the
  button and its question in Chromium with those answers and reads the grid back: every new
  folder on the tiles, *Sort the rest* shown, the trial posted once. Measured locally:
  1 passed in 2.5 s (browser image cached).
