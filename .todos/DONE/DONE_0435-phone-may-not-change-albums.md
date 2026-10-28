# 0435 — A paired phone may no longer change an album (strict read-only)

- **Priority**: Medium
- **Batch**: phone
- **Depends**: —
- **Files**: `src/media_hygiene/review/lan_paths.py`, `src/media_hygiene/share/album_page.py`, `src/media_hygiene/review/write_routes.py`, `tests/unit/` (the 0429 guard test), the album page templates (`review/templates/album_*`), `documentation/en/commands/home.md`, `documentation/fr/commands/home.md`

## Why

Review of the 2026-10-27 iterate (question 1, maintainer): 0427 kept `POST /api/albums` (writes
`albums.json`, no photo moved) open to a paired phone. Decided: **forbid it**: off the PC
everything is read-only (memory `phone-read-only`), albums included.

## What

- Drop `albums.PHONE_WRITES` from `lan_paths.WRITE_PATHS`: a phone's album change gets the
  read-only 403, as every other write.
- The 0429 guard lists the album routes with the other write routes (no exception left).
- On the phone, the album page shows no write control (create, rename, add, remove, cover);
  the albums stay viewable (cover, days, full screen).
- Docs en+fr: albums are made on the PC; the phone shows them.

## Explicit NON-goals

- Any album feature on the PC.
