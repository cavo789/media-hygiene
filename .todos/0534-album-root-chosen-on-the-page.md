# 0534 — Albums folder chosen on the albums page

- **Priority**: High
- **Batch**: one-interface
- **Depends**: —
- **Files**: `src/media_hygiene/review/templates/album_bar.html.j2`, `src/media_hygiene/places/toml_edit.py`, `documentation/en/`, `documentation/fr/`

## Asked (maintainer, 2026-10-30)

"If this feature is not shown in the web interface, it is as if it did not exist." Each setting
is placed **on the page where it acts**, next to its visible effect (no catch-all settings page),
saved with `places/toml_edit` (comments kept, atomic) and **read back from disk** before being
shown. Follows 0532 (folder roles); analysed in detail at implementation time.

## Wanted

`[album] root` empty: the albums page asks "Where should your albums go?" with a folder chooser;
set: shown in the bar with *Change* (what happens to existing albums when it changes: to decide).

## Decided (2026-11-02)

By the maintainer, review of the 2026-11-02 iterate: when the albums folder changes, the album
link folders are **recreated in the new folder**; the old folder is emptied of its links only
(never a photo, never a file the tool did not make), and `albums.json` keeps the albums.
