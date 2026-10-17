# 0231 — `places`: the folders named after a town, checked and placed on the map, saved in `config.toml`

- **Priority**: Medium
- **Batch**: places
- **Depends**: 0230
- **Files**: `src/media_hygiene/places/folders.py` (new), `src/media_hygiene/places/board.py`, `src/media_hygiene/places/app.py`, `src/media_hygiene/places/config_file.py`, `src/media_hygiene/places/templates/places.html.j2`, `src/media_hygiene/services/places.py`, `src/media_hygiene/config/places_settings.py`, `src/media_hygiene/services/xmp_towns.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/integration/test_places_folders.py` (new), `documentation/en/commands/places.md`, `documentation/fr/commands/places.md`, `documentation/en/commands/xmp.md`, `documentation/fr/commands/xmp.md`

## Wish

Maintainer, 2026-10-17: in `mh places`, see the folders named after a town (`Douarnenez`,
`Saint-Jean de Luz`) to locate their photos on the map; the position then goes into the `.xmp`
sidecars (0230). Chosen: an adjusted position is saved in `config.toml`, `[[places.folders]]`.

## To do

1. A third folding list on the page, "Folders named after a town (N)": one line per folder the
   0230 guess names (`Douarnenez — 37 photos without GPS`), the largest first. A click centres
   the map on the town, shows a draggable pin and the folder's photos (the grid of 0226).
2. On that line: **Save this position** writes `[[places.folders]]` (`folder` as a host path,
   like `protected`; `latitude`, `longitude`) into `config.toml` with tomlkit (comments kept,
   read back and shown, as the places are); **Not a town** adds the folder's name to
   `[classify] folder_town_ignore` (read back too).
3. `xmp` (0230) takes a `[[places.folders]]` position before the town's centre; such a folder
   needs no town name (any folder may be placed: a folder line of the photo grid, or the map
   clicked while a folder is chosen).
4. A saved folder that no longer exists (renamed in Explorer, moved by `sort`): listed apart on
   the page ("not found: rename or delete"), never an error; `xmp` says it once.
5. Tests: save then read back; not a town; a folder moved; host ↔ container paths.
6. Docs EN + FR (`commands/places.md`, `commands/xmp.md`); `i18n_update`; `docs_screenshots` to run.

## Explicit non-goals

- Photos of folders without a town name, placed one by one: only whole folders here.

## Status — PARTIAL (2026-10-17)

### Done
- A third folding list on the map, "Folders named after a town (N)" (`places/folder_rows.py`,
  `places/folders.py`): the folders the `folder_town` guess names that hold photos without GPS,
  plus every `[[places.folders]]` entry; the most photos first; 📁 / 📌 saved / ⚠ not found.
  A click centres the map, drops a draggable green pin (saved position or the town's centre)
  and shows the folder's pictures without GPS (24 at most, the grid of 0226).
- `POST /api/folder` (`save` / `forget` / `ignore`), only for a folder of the list; each answer
  is the list read again from `config.toml` (`places/config_folders.py`, tomlkit, comments kept,
  checked then replaced atomically). `[[places.folders]]` (`folder` host path as a literal
  string, `latitude`, `longitude`); `ignore` adds the folder's name to
  `[classify] folder_town_ignore` once whatever its spelling (`town_key`).
- `[places] folders` setting (`FolderPosition`), commented example in the default `config.toml`.
- `xmp` (0230) takes the nearest folder above a photo: a saved position first, else the town's
  centre; a saved folder needs no town name; a saved folder not found is said once
  (`xmp_view`), never an error. The index is read once for the clusters and the folders
  (`services/places_index.py`); the clusters now count Takeout positions too.
- Tests: `tests/integration/test_places_folders.py` (listed with previews and a 404; save,
  forget, ignore read back; an unknown folder refused with a reason; a saved folder renamed:
  not found, `xmp` warns; `xmp --apply` writes the saved position). Page script syntax checked
  with node 20 (Docker); no browser test.
- Docs EN + FR (`commands/places.md`, `commands/xmp.md`); French catalog.

### Not done
- Placing a folder whose name is no town from the page (the TODO's "a folder line of the photo
  grid, or the map clicked while a folder is chosen").
  **Reason:** needs a way to pick any folder on the page (a folder picker, or the cluster grid
  naming its folders); a design choice for the maintainer. Such a folder can be written by
  hand in `[[places.folders]]` today, and `xmp` and the page already use it.
- The documentation captures of `places` (the new list) and of the default `config.toml`.
  **Reason:** `docs_screenshots` not run (heavy, run on request).
