# 0301 — browse: show photos or videos only, sort by size

- **Priority**: Medium
- **Batch**: review-ui
- **Depends**: —
- **Files**: `src/media_hygiene/search/folders.py`, `src/media_hygiene/search/templates/browse.html.j2`, `src/media_hygiene/search/templates/browse.js.j2`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/commands/browse.md`, `documentation/fr/commands/browse.md`, `tests/integration/tags/test_browse_page.py`

## Why

The maintainer, testing `mh browse` on 2026-10-22, wanted to see which videos are huge so they
could convert them. Neither was possible: **Sort by** offers only `name` and `date`, and nothing
shows the videos alone. The size of every file is already in the index (`FOLDER_FILES` reads
`size`), but it is only displayed (`human_size`), never used to sort.

This TODO covers **one folder at a time**, the page's design. 0302 adds the view of the whole
library (the real need: the heaviest videos wherever they are).

## What

- `FolderAsked` (`search/folders.py`): `order: Literal["name", "date", "size"]`, with `size` the
  largest first and ties broken by name (casefold), like the other orders. A new field
  `kind: Literal["all", "photos", "videos"] = "all"` keeps only the photos (image + RAW, as
  `folder_tree._PHOTOS` counts them) or only the videos (`media_kind`). Sort on the raw byte
  count: never on the `human_size` text.
- The page: a third `<option>` **size** under **Sort by**, and a **Show** select (All / Photos /
  Videos) next to it, which reopens the folder like `order` does (`browse.js.j2`). Ctrl+A, Shift+click
  and ←/→ in the viewer work on the files shown, never on the hidden ones.
- When the filter empties a folder that holds files, say so ("No video in this folder (12
  photos)") instead of an empty grid.
- Remember the two choices for this viewer only (`localStorage`, wrapped in try/catch) so that
  opening another folder keeps them.
- The tree's counts are unchanged (they already show photos and videos apart).

## Tests

- `size` order: largest first, equal sizes by name; `kind=videos` leaves out a `.jpg` and a
  `.cr2`, `kind=photos` leaves out a `.mp4`; an unknown `kind` or `order` → 400.
- A file set aside stays marked once filtered.

## Docs

`commands/browse.md` in both languages (**Sort by** / **Trier par**, **Show** / **Afficher**).
The page changes: `docs_screenshots` should run afterwards (not unasked).
