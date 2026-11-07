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

- [ ] Going to the next event shows its thumbnails without a visible wait (prefetched)
- [ ] Reopening the tab returns to the last event shown, per tab (`sessionStorage`) or saved, said which
