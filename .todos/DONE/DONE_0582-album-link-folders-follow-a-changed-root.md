# 0582 — Album link folders follow a changed albums folder

- **Priority**: Medium
- **Batch**: one-interface
- **Depends**: 0534
- **Files**: `src/media_hygiene/search/album_root_desk.py`, `src/media_hygiene/services/album.py`, `src/media_hygiene/actions/album.py`, `tests/unit/`, `documentation/en/commands/search.md`, `documentation/fr/commands/search.md`

## Why

Decided by the maintainer (2026-11-02, in 0534): when `[album] root` changes, the album link
folders are recreated in the new folder; the old folder is emptied of its links only (never a
photo, never a file the tool did not make), and `albums.json` keeps the albums. 0534 saves the
new root from the page but leaves the folders made before where they are.

## To do

1. After a change of root on the page, offer "Move the N album folders made in {old}" (count
   stated): a journaled album run per album into the new root (undoable by `undo`), then the
   links the journal proves the tool made removed from the old folder, empty folders removed.
2. A file in the old folder that the journal does not list stays, said.
3. Tests: moved, undone, a foreign file kept, a folder renamed in Explorer meanwhile.

## Where the user gains

Before: each album remade by hand with `mh album <name> --apply`. After: one click.
