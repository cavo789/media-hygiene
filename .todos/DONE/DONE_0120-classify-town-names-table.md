# 0120 — `[classify.town_names]`: rename GeoNames towns (Brussels → Bruxelles, Brugge → Bruges)

- **Priority**: Low
- **Batch**: classify
- **Depends**: —
- **Files**: `src/media_hygiene/config/classify_settings.py`, `src/media_hygiene/config/templates/config.toml.j2`, `src/media_hygiene/geo/gazetteer.py`, `src/media_hygiene/classify/trips.py`, `documentation/en/sort/09-places-from-gps.md`, `documentation/fr/sort/09-places-from-gps.md`

## Context

PARTIAL 0030: GeoNames names towns in English or in their local language (`Turin`, `Munich`,
`Brussels`, `Brugge`); `trip` categories then read `Italie/Turin`, `Belgique/Brugge`. Decided
in review 0056 (2026-10-12): a table in `config.toml`, applied wherever a town name appears.

## What to do

- `[classify.town_names]`: `"Brugge" = "Bruges"`, `"Torino" = "Turin"` … (exact GeoNames name →
  the user's name). Validated by pydantic (non-empty strings).
- Applied when a town is named: `trip` categories, `{city}` in layouts, the workbook, the
  `places` page labels, and the folder-town rule of 0119 (which must also *match* the user's
  name: `Bruges` folder → Brugge's coordinates).
- A commented example in `config.toml.j2` (en + fr catalogue).
- Docs en + fr.

## Explicit NON-goals

- Shipping GeoNames alternate names (snapshot size): only the user's table.

## Acceptance

- Tests: a renamed town in a trip category and in `{city}`; an unknown key is harmless.
