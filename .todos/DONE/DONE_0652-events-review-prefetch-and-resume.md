# 0652 — Events tab: next event's thumbnails ready, reopened on the last event shown

- **Priority**: Low
- **Batch**: events
- **Depends**: —
- **Files**: `src/media_hygiene/search/templates/`, `src/media_hygiene/review/events_*.py`

## Problem

Left from 0438 (listed as "not ported" in 0446): the former events review preloaded the next
event's thumbnails and reopened on the last event shown; the Events tab of `library` does neither.

## Decided (2026-11-07, maintainer, review of the iterate of 2026-11-07 (2))

File both: no wait between two events, and the tab resumes where the user stopped.

## Acceptance

- [x] Going to the next event shows its thumbnails without a visible wait (prefetched)
- [x] Reopening the tab returns to the last event shown, per tab (`sessionStorage`) or saved, said which

## Outcome

DONE: `search_events_ahead.js.j2` prefetches the next visible event (its JSON and first 60 thumbnails as `Image`s) after each grid, plan and index events; the last event shown is kept in `sessionStorage` (per browser tab, said in the docs) and resumed when the list loads. Test: `tests/unit/test_events_ahead.py`.
