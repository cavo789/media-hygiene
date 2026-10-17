# 0236 — `places`: "Your places" sorted by name, home first

- **Priority**: Low
- **Batch**: places
- **Depends**: —
- **Files**: `src/media_hygiene/places/templates/places.html.j2`, `tests/unit/test_places_page.py`, `documentation/en/commands/places.md`, `documentation/fr/commands/places.md`

## Seen

Maintainer, 2026-10-17: the "Your places" list follows the order of `config.toml`
(`draw()` iterates `state.places` as written): hard to find a place among many. Wished: sorted
alphabetically, the home place (`home = true`, "Maison") first.

## To do

1. In `draw()`, the list (not `state.places`, whose index is each place's `key` in the file)
   sorted: home first, then by name with `localeCompare(…, document.documentElement.lang,
   {sensitivity: "base"})` so that "Écluse" sorts with E and case is ignored.
2. The file's order is unchanged (tomlkit keeps each place where it is): only the page sorts.
3. A place just saved still flashes in its sorted position (`flashName`).
4. Test (page test): the order of the rendered list with a home place, accents and lower case.
5. Docs EN + FR if the order is described; `docs_screenshots` to run.
