# 0234 — `places`: a cluster not worth a name, set aside with ✕ (and back)

- **Priority**: Medium
- **Batch**: places
- **Depends**: —
- **Files**: `src/media_hygiene/config/places_settings.py`, `src/media_hygiene/places/config_folders.py`, `src/media_hygiene/places/board.py`, `src/media_hygiene/places/app.py`, `src/media_hygiene/places/clusters.py`, `src/media_hygiene/places/templates/places.html.j2`, `src/media_hygiene/config/templates/config.toml.j2`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/unit/test_places_clusters.py`, `tests/integration/test_places_command.py`, `documentation/en/commands/places.md`, `documentation/fr/commands/places.md`

## Seen

Maintainer, 2026-10-17 (`mh places`, screenshot): a cluster shows two children in a car, "the
place is not relevant". There is no way to say so: the cluster stays in "The largest clusters
without a name" for ever and pushes the next ones down (`SHOWN_CLUSTERS = 15`).

## To do

1. An **✕** at the end of each cluster line (tooltip "Not a place worth a name"); a click sets it
   aside at once (no confirmation: the undo below is one click), the list and the map redraw.
2. Saved in `config.toml`, `[[places.ignored]]` (`latitude`, `longitude`, `radius_m`, default
   150 m), with tomlkit like `[[places.folders]]` (comments kept, atomic, read back and shown) —
   never elsewhere under `/config`. A position, not a cell rank: the rank and the 200 m grid
   (`CELL_DEGREES`) may change between versions.
3. A cluster whose middle lies within an ignored circle is left out of the unnamed list and
   **hidden** from the map (decided below); only the "Set aside" fold shows it.
4. A fourth folding list, folded by default: "Set aside (N)", one line per entry, **Restore**
   takes it out of `config.toml`.
5. `classify` is unchanged: a set-aside cluster is just unnamed (town fallback, `trip` rules
   apply). Said in the docs.
6. Tests: set aside, read back, restore; a later audit moving the cluster's middle by a few
   metres still matches; two clusters inside one ignored circle; the file's comments kept.
7. `config.toml` template comment, `i18n_update`, docs EN + FR; `docs_screenshots` to run.

## Setting

`radius_m` per entry is the setting; a global default in `[places]` only if the review asks.

## Decided (2026-10-17)

- The maintainer: a set-aside cluster is hidden from the map (not drawn faint).
