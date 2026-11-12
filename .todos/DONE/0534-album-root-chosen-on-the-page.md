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

## Status — PARTIAL (2026-11-03)

### Done
- The album bar of `search`/`browse` says where the albums go (`[album] root`, else `Albums` in
  `[classify] target`), read from `config.toml`; empty, it asks "Where should your albums go?";
  *📁 Change* opens a folder field. `GET`/`POST /api/album-root` (`search/album_root_desk.py`):
  refused (409, file untouched) outside the mounted folders, inside a protected one, or
  read-only; saved with `toml_edit`, read back and said. Tests `tests/unit/test_album_root_desk.py`.
  Docs `commands/search.md` EN + FR.

### Not done
- The decided move: album link folders recreated in the new folder, the old one emptied of its
  → code work, not the maintainer's: listed in 0718 (2026-11-12)
  links only. **Reason:** needs a journaled run (links made then removed, undoable), out of a
  page request; filed as 0582. Until then the answer says the folders made before stay, and to
  run `mh album <name> --apply` again.
- A tree folder chooser (the field is a typed path). **Reason:** the search tree lists the
  → code work, not the maintainer's: listed in 0718 (2026-11-12)
  library folders only; an album folder is often a new one.
- `docs_screenshots` to refresh the search captures (not run: heavy).
  → captures: one run of `docs_screenshots`, tracked in 0717 (2026-11-12)

## Closed by the inbox (2026-11-12)

Nothing left for the maintainer: each item above is answered (`→`); the code work left is
listed in 0718, the captures in 0717.
