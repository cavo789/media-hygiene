# 0030 — Places from GPS: personal places, offline reverse geocoding, a map page to name them

- **Priority**: Low — only 1.3 % of the maintainer's photos carry GPS; worth it for recent phones and other users
- **Batch**: geo
- **Depends**: 0025, 0026, 0033, 0035
- **Files**: `src/media_hygiene/geo/` (new: geocoder, places, clusters, data), `src/media_hygiene/classify/rules/`, `src/media_hygiene/config/settings.py`, `src/media_hygiene/cli/cmd_places.py`, `src/media_hygiene/services/places.py`, `src/media_hygiene/places/` (new: app, templates, vendored Leaflet), `src/media_hygiene/review/http.py`, `pyproject.toml` (tomlkit), `.devcontainer/helpers/`, `documentation/en/`, `documentation/fr/`

## Context

With GPS, a photo can say "Maison", "Chez papy", or "Italie/Turin" without any AI. On the
maintainer's collection only 1.3 % of images have coordinates: recent iPhones record them,
older Android phones did not. The feature stays useful but is not the backbone of `classify`
(0026). It adds the `place` and `trip` rule kinds to the rules of 0035.

## Proposal

**Personal places** in `[[classify.places]]`:
- `name`, `latitude`, `longitude`, `radius_m`;
- one of them can be `home = true`, the reference for trips.

The radius exists only for these places: a city name cannot tell home from the bakery next door.
An area taken from OpenStreetMap instead of a circle (a village, a municipality) is 0044.

**Offline reverse geocoding**: public GeoNames data (CC-BY 4.0, attribution in the docs).
- Countries, first-level regions, and cities of more than 1,000 inhabitants (~150,000).
- Nearest neighbour with numpy (already a dependency). No coordinate leaves the machine.
- Shipping the data is to decide at implementation:
  - (a) a processed snapshot in the package, refreshed by a devcontainer helper — reproducible,
    works in tests offline (with a tiny fixture);
  - (b) a download in a Dockerfile stage — GeoNames dumps have no versioned URL, so the build
    is not reproducible.

  Prefer (a).
- Country names in fr and en are produced when the snapshot is made, never at runtime. City
  names are GeoNames' (often English exonyms: Turin, Munich); a user alias table renames them.

**Rules**:
- `place`: within a personal place's radius.
- `trip`: an event (0026) farther than `trip_min_km` from home. Its category comes from
  `trip_category`, default `{country}/{city}`.
- Photos without GPS inside such an event inherit it (`trip-neighbour`, lower score).
- **Trips over several days** *(sorta)*: the events of 0026 closer than `trip_merge_gap_hours`
  (48) whose coordinates lie within `trip_merge_max_km` (120) form one trip. By distance, not
  by city: a trip through villages would otherwise fall into pieces.
- **A place from a folder name** *(sorta's `path_inferred`)*: a meaningful folder label that
  matches a GeoNames city or country (`2017/Janvier 2017/Bruges`) gives the place to the files
  without GPS under it (`folder-place`, lower score than GPS). This is where the maintainer's
  collection has its places: in folder names, not in coordinates.

**`places` command**: a local map page served like `review` (reuses `review/http.py`: loopback
only, `-p 127.0.0.1::8080`).
- The map shows **clusters of the user's photos** from the index, as circles sized by count.
  The biggest unnamed clusters are listed first: home is usually the first.
- Click a cluster or the map, name the point, set the radius with a slider or by dragging the
  circle; move or delete a place.
- The search is offline, among GeoNames cities, and zooms there (an explicit online search
  is 0044).
- Leaflet (BSD-2) is vendored in the package. Only map **tiles** are fetched by the browser
  (OpenStreetMap by default, URL configurable, attribution shown). They reveal the areas
  viewed, never a photo or a list of coordinates. The CSP allows that tile host only.
- Saves into `config.toml` with `tomlkit`, which keeps the user's comments and layout. The
  write is atomic and needs a writable `/config`. Names are validated: unique, Windows-safe
  (they become folder names).

## Acceptance

- [ ] Unit tests: nearest city on a tiny fixture, radius match, trip detection, inheritance.
- [ ] `places` saves a place into a commented `config.toml` without losing a comment (test).
- [ ] Documentation en + fr with fictitious coordinates only (public repository); `.po`
      translated.

## Status — PARTIAL (2026-10-02)

### Done
- `[[classify.places]]` (name, latitude, longitude, radius_m, home), validated: unique,
  Windows-safe names, one home; `trip_min_km`, `trip_merge_gap_hours`, `trip_merge_max_km` in
  `[classify]`.
- Rules `place` and `trip` (`classify/whereabouts.py`, `trips.py`, `trip_walk.py`), reasons
  `place`, `place-neighbour`, `trip`, `trip-neighbour`; files without GPS inherit from their
  event (score 70, "to check"); trips merged by time and distance, named after the largest town
  within 10 km of their largest located event; `{place}`, `{country}`, `{region}`, `{city}`
  placeholders filled. The trip category is the rule's own `category` (default
  `{country}/{city}`) rather than a separate `trip_category`.
- Offline reverse geocoding: option (a), a processed GeoNames snapshot vendored in
  `src/media_hygiene/geo/data/` (161,547 towns, 1.67 MB xz, CC BY 4.0 in `ATTRIBUTION.txt`),
  rebuilt by the `geonames_update` helper (`tests/support/geonames/`); country names fr/en from
  CLDR at snapshot time; numpy nearest neighbour on a one-degree grid; tests use a tiny
  snapshot built from a fake dump.
- `media-hygiene places`: Leaflet 1.9.4 vendored (BSD-2), clusters of the index, offline town
  search, loopback-only server reusing `review/http.py` (+ `review/serving.py`), CSP allowing
  the `[places] tiles` host only, places saved with tomlkit (comments kept, atomic).
- Tests (unit + integration), docs en + fr (`sort/09-places-from-gps.md`), `.po` translated.
  Image: +2.67 MB (278,891,713 → 281,563,039 bytes).

### Not done
- A place from a folder name (`folder-place`, sorta's `path_inferred`).
  **Reason:** needs a maintainer decision: with 160,000 town names, ordinary folder words
  collide with real towns (Mons, Spa, Nice…); population threshold, countries only, a user
  alias list, or an opt-in low-score rule? And which category: the folder's label (already kept
  by `existing_folder`) or `{country}/{city}`?
- A user alias table renaming GeoNames town names (Turin → Torino).
  **Reason:** not built; a `trip` rule's `category` template already lets the user word the
  folder; to decide whether a `[classify]` alias table is still wanted.
- `docs_screenshots` and `e2e` were not run.
  **Reason:** after a PC reboot, `docker run` dropped every attached output written later than
  about 1 s (environment issue); the two `--help` capture blocks touched were filled from the
  sources. Run both once Docker works again; no screenshot of the map page was added (it would
  fetch real OSM tiles while the docs are generated: maintainer's choice).
