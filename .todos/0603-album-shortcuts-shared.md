# 0603 — Phone album shortcuts shared between phones, stored on the PC

- **Priority**: Low
- **Batch**: phone
- **Depends**: 0548 (DONE)
- **Files**: `src/media_hygiene/review/` (TV slot, albums page), `albums.json`

## Why (review of feedback-2026-11-03-iterate (2026-11-05))

0548 keeps the 3 last albums shown on the TV in each phone's storage (`mh-home-tvRecent`). Decided: share them through the PC — a `last_shown` per album written by the PC when the TV starts an album (the PC writes, not the phone: the phone stays read-only), read by every phone's home page and the albums page's sort.
