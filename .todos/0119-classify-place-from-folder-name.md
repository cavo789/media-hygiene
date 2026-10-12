# 0119 — `classify`: a town named by a folder (`2017/Durbuy`) as a low-score place signal

- **Priority**: Low
- **Batch**: classify
- **Depends**: 0120
- **Files**: `src/media_hygiene/classify/rules/`, `src/media_hygiene/classify/whereabouts.py`, `src/media_hygiene/geo/gazetteer.py`, `src/media_hygiene/config/classify_settings.py`, `src/media_hygiene/config/templates/config.toml.j2`, `documentation/en/sort/09-places-from-gps.md`, `documentation/fr/sort/09-places-from-gps.md`

## Context

PARTIAL 0030 left "place from a folder name" open. Most of the maintainer's photos have no GPS
(1.3 %), and folder names carry the meaning (`2017/…/Durbuy`, `Juillet 2011/Italie`). Decided
in review 0056 (2026-10-12): a population threshold **with guards**, category
`{country}/{city}` like the `trip` rule.

Measured on the vendored GeoNames snapshot: a threshold alone fails both ways — `Nice` (FR,
342k), `Paradise` (US, 223k), `Normal` (US, 54k), `Mons` (BE, 95k) would match ordinary words,
while real destinations `Durbuy` and `Spa` have 10k. `Bruges` resolves to Bruges in Gironde
(FR, 12k): GeoNames lists the Belgian town as `Brugge` (see 0120 for names in the user's
language).

## What to do

A new rule `match = "folder_town"` (name to settle), opt-in in the default `config.toml`:

- A folder name matches only when it **equals** a town name (case- and accent-insensitive),
  never a word inside it.
- `min_population` (default 5,000) filters the candidates.
- Among homonyms, prefer the countries of the collection's GPS photos (and `home`'s country);
  otherwise the most populous.
- Ignored when GPS photos of the same folder are farther than `trip_merge_max_km` from the
  town.
- Low score by default (below `sure`, e.g. 60): proposals land in "À vérifier"; any other rule
  wins.
- Category template `{country}/{city}`, overridable by `category`.

## Explicit NON-goals

- Country names alone, region names, aliases typed by the user (rejected options).
- Network lookups: GeoNames offline only.

## Acceptance

- Tests: `2017/Durbuy` → Belgique/Durbuy; `Nice` folder with GPS photos in Belgium → ignored;
  `Vacances` → nothing; a folder named like a 3k town → nothing at the default threshold.
- Docs en + fr in `sort/09-places-from-gps.md`, the commented rule in `config.toml.j2`.
