# 0242 — `places`: place any folder (not named after a town) from a folder list of the page

- **Priority**: Medium
- **Batch**: places
- **Depends**: —
- **Files**: `src/media_hygiene/places/app.py`, `src/media_hygiene/places/posts.py`, `src/media_hygiene/places/folders.py`, `src/media_hygiene/places/folder_rows.py`, `src/media_hygiene/places/config_folders.py`, `src/media_hygiene/places/templates/places.html.j2`, `src/media_hygiene/search/folder_tree.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/integration/test_places_folders.py`, `documentation/en/commands/places.md`, `documentation/fr/commands/places.md`

## Context

Follows 0231 (PARTIAL): the page places only the folders whose name is a town guess
(`folder_town`); a folder such as `Mariage Julie` with photos without GPS can only be written by
hand in `[[places.folders]]` of `config.toml`, which `xmp` and the page already read. Decided by
the maintainer (inbox, 2026-10-19): a list of every folder, as `browse` shows them (0223,
`search/folder_tree.py`), rather than the cluster grid naming its folders.

## What to do

- A fourth folding list on the map, "Any folder", built from the index's folder tree
  (`search/folder_tree.py`: reuse it, do not walk the disk): mounted folders open, the rest
  closed; each folder with its count of photos **without GPS** (the ones a position helps);
  folders with none greyed. Filter box as the other lists (0238).
- A click: the same panel as a town folder (0231): its pictures without GPS (24 at most),
  then a click on the map or the draggable pin saves `[[places.folders]]` through the same
  `POST /api/folder` path (`save` / `forget`), read back from `config.toml` and shown. A folder
  already saved moves to *Placed* (0238).
- `POST /api/folder` accepts any folder of the index's tree, still refuses a folder unknown to
  the index (with its reason); the host path written as today (literal string).
- Path-keyed (workflow rule): a placed folder renamed or moved — by `sort` or in Explorer — is
  "not found" as for 0231 (`xmp` warns once); test it.

## Acceptance

- Integration: a folder with no town name listed, saved, read back, used by `xmp --apply`;
  an unknown folder refused; a renamed folder said not found.
- Size caps: `places/` modules near 200 lines — run `.claude/scripts/near_limit.sh` first and
  plan a new module (e.g. `places/tree_rows.py`).
- Docs both languages: `commands/places.md`.

## Gain (estimated)

Every event folder without GPS (weddings, holidays named after people) placed in two clicks
instead of a hand-written `config.toml` block.
