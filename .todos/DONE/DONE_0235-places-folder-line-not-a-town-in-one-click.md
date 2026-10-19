# 0235 — `places`: "Not a town" in one click on a folder line (Léo is the cat)

- **Priority**: Medium
- **Batch**: places
- **Depends**: 0234
- **Files**: `src/media_hygiene/places/templates/places.html.j2`, `src/media_hygiene/places/folders.py`, `src/media_hygiene/places/config_folders.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/integration/test_places_folders.py`, `documentation/en/commands/places.md`, `documentation/fr/commands/places.md`

## Seen

Maintainer, 2026-10-17 (`mh places`, screenshot): "Folders named after a town (53)" lists
**Léo — 193 photos without GPS**. Léo is the family cat, not a town (a GeoNames town of that
name passes `folder_town_min_population`). "I should be able to delete this line here."

The action exists since 0231 (**Not a town**, `[classify] folder_town_ignore`), but only in the
panel a click on the line opens, under its photos: not found from the list.

## To do

1. An **✕** at the end of each folder line whose name is a town guess (tooltip "Not a town:
   never read as one"), the same look as the cluster lines' ✕ (0234); a click adds the name to
   `folder_town_ignore` (the existing `POST /api/folder`, `action: "ignore"`), read back, the
   line disappears, the status says "Léo: never a town again (config.toml)".
2. A line with a saved position (📌) gets no ✕ (its position is the user's, **Forget its
   position** stays in the panel).
3. Undo: the set-aside names listed in the "Set aside (N)" fold of 0234, **Restore** takes the
   name out of `folder_town_ignore`.
4. The name is ignored everywhere (`Léo` in any folder), as `folder_town_ignore` already is: the
   tooltip says it.
5. Tests: ignore from the line, restore, the comments of `config.toml` kept.
6. `i18n_update`; docs EN + FR; `docs_screenshots` to run.
