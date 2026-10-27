# 0371 — An album's cover chosen by the user

- **Priority**: Low
- **Batch**: share
- **Depends**: —
- **Files**: `src/media_hygiene/share/albums.py`, `src/media_hygiene/share/album_view.py`, `src/media_hygiene/share/album_api.py`, `src/media_hygiene/share/templates/album.js.j2`, `src/media_hygiene/share/templates/album.html.j2`, `tests/integration/test_album_phone.py`, `documentation/en/commands/share.md`, `documentation/fr/commands/share.md`

## Context

Review of the feedback of 2026-10-22 (0297), maintainer 2026-10-25. The cover is chosen by the
tool: the sharpest photo of the first day (`album_view._cover`). The user cannot pick the photo
that sums up the holiday.

## What to do

1. `albums.json` schema 2: an optional `cover` per album (the entry's SHA-256 and size, followed
   when the file moves like any entry); schema 1 still read, written as 2 at the next change.
2. The large view of the album page: *Use as cover*; the change read back from disk and shown.
3. A cover taken out of the album, or not found: back to today's choice, silently.
4. Tests: chosen → shown; moved → still found; removed from the album → today's cover; a
   schema 1 file read. Docs en + fr.

## Acceptance

- The cover chosen on the phone is the one shown on the albums' list, after a restart too.
