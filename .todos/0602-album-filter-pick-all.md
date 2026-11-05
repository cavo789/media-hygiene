# 0602 — Pick all N found works with the album filter

- **Priority**: Low
- **Batch**: library
- **Depends**: 0501 (DONE)
- **Files**: `src/media_hygiene/review/` (`/api/chosen`, `/api/albums`)

## Why (review of feedback-2026-11-03-iterate (2026-11-05))

With the album filter on, search does not offer *Pick all N found* (the "all" re-runs of `/api/chosen` and `/api/albums` ignore the album). Decided: both pickers read `albums.json` so the count and the set match what the filter shows (never act on hidden).
