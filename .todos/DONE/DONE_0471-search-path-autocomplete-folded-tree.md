# 0471 — Search: folder autocomplete on the path field, *My folders* folded

- **Priority**: Medium
- **Batch**: search
- **Depends**: 0465
- **Files**: `src/media_hygiene/search/templates/search.html.j2`, `src/media_hygiene/search/templates/search.js.j2`, `src/media_hygiene/search/templates/search_folders.js.j2`, `src/media_hygiene/search/folders.py`, `src/media_hygiene/search/folder_tree.py`

## Why

The maintainer, 2026-10-29: pick a folder without scrolling the tree; more room for photos.

## Decided (2026-10-29, the maintainer)

- *Path contains* gets an autocomplete: a click on the empty field lists the folders (most
  files first, with their count); typing narrows the list (substring, case-insensitive). Free
  text (`*.mp4`, a regex) still works: the list is a help, never a constraint.
- *My folders* is not removed: it folds to one fixed line « 📁 My folders ▸ » that opens as a
  floating panel (like *More keys*); the line keeps its place (the screen never jumps).
- Later, after some weeks of use: remove the tree if it is never opened (a new TODO then).

## Acceptance

- Keyboard: ↓/↑ to move in the list, Enter picks, Esc closes; the grid does not move.
- Folder list from the index (no disk walk at each key); i18n FR; docs EN+FR.
