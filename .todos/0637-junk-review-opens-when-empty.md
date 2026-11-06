# 0637 — Unwanted review opens even when nothing is listed, with its sliders

- **Priority**: Low
- **Batch**: review
- **Depends**: —
- **Files**: `src/media_hygiene/services/review_here.py`, `src/media_hygiene/cli/`

## Problem

Follows 0537. `review --junk` does not open when no photo is listed, so its thresholds cannot be
loosened from the page.

## Decided (2026-11-06, maintainer, review of the iterate of 2026-11-06 (2))

Open it anyway: "Nothing found" with the strictness sliders beside it, to widen the search.

## Acceptance

- [ ] An empty review opens a page with the sliders; moving one lists what enters (test)
- [ ] Both languages of the docs updated; `docs_screenshots` flagged as stale
