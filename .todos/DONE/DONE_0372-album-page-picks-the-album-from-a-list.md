# 0372 — Album page: *Add to an album* picks from the list of albums

- **Priority**: Low
- **Batch**: share
- **Depends**: —
- **Files**: `src/media_hygiene/share/templates/album.js.j2`, `src/media_hygiene/share/templates/album.html.j2`, `src/media_hygiene/share/album_api.py`, `tests/integration/test_album_phone.py`

## Context

Review of the feedback of 2026-10-22 (0297), maintainer 2026-10-25. Adding the photo shown to
another album asks its name with `window.prompt` (`album.js.j2`, `change`): a typo makes a second
album, and a phone's prompt hides the photo.

## What to do

1. A small sheet listing the saved albums (most recent first), then *New album…* with a field.
2. The answer read back from disk (`albums.json`) and said, as today.
3. Tests: add to an existing album from the list; a new name; the same name in another case
   → the existing album (as `album` matches names). Docs: the album page's paragraph, en + fr.

## Acceptance

- On the phone, adding a photo to an album takes two taps and never makes an unwanted album.
