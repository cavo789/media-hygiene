# 0229 — Town names match across hyphens, spaces and apostrophes: `Saint-Jean de Luz` is Saint-Jean-de-Luz

- **Priority**: High — a folder named after a town is silently not recognised
- **Batch**: classify
- **Depends**: —
- **Files**: `src/media_hygiene/geo/folding.py`, `src/media_hygiene/geo/gazetteer.py`, `src/media_hygiene/classify/folder_towns.py`, `tests/unit/test_classify_folder_towns.py`, `tests/unit/test_geo_folding.py` (new), `documentation/en/sort/09-places-from-gps.md`, `documentation/fr/sort/09-places-from-gps.md`

## Problem

Maintainer, 2026-10-17: folders named `Douarnenez`, `Saint-Jean de Luz`. Measured in the
devcontainer (`Gazetteer.load().search(…)`): `Douarnenez` and `Saint-Jean-de-Luz` are found,
`Saint-Jean de Luz` is not. `geo/folding.fold` removes case and accents only, so a space where
GeoNames writes a hyphen (or an apostrophe, `L'Isle-Adam` / `L Isle Adam`, a typographic `’`)
breaks the `folder_town` rule of `classify` and the town search of `places`.

## To do

1. A `town_key(text)` next to `fold`: folded, then hyphens, apostrophes (`'`, `’`), underscores
   and dots read as spaces, runs of spaces collapsed. `fold` itself stays as it is (101 callers
   compare other things with it).
2. Use it where a typed or folder name meets a town name: `folder_towns._towns` / `named`
   (keys and lookup), `folder_town_ignore`, `Gazetteer.search` (prefix search), and the user's
   `town_names` renaming if it compares names.
3. Tests: `Saint-Jean de Luz`, `saint jean de luz`, `Saint_Jean_de_Luz` find Saint-Jean-de-Luz;
   `L'Isle-Adam` with `’`; a month name still is never a town; `folder_town_ignore =
   ["Saint Jean de Luz"]` ignores the hyphenated folder too.
4. Docs EN + FR (step 9, the `folder_town` bullets): spaces, hyphens and apostrophes do not matter.

## Explicit non-goals

- Abbreviations (`St-Jean`, `Ste-`): to see later if the maintainer meets them.
