# 0044 — A personal place drawn from an OpenStreetMap area (Nominatim search, opt-in)

- **Priority**: Low — same reason as 0030: few photos carry GPS
- **Batch**: geo
- **Depends**: 0030
- **Files**: `src/media_hygiene/geo/nominatim.py` (new), `src/media_hygiene/geo/areas.py` (new), `src/media_hygiene/geo/places.py`, `src/media_hygiene/places/` (search, templates), `src/media_hygiene/config/settings.py`, `src/media_hygiene/config/templates/config.toml.j2`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/`, `documentation/fr/`

## Context

0030 plans personal places as circles (`latitude`, `longitude`, `radius_m`) and an offline
search among GeoNames cities of more than 1,000 inhabitants. A village or a municipality is
not a circle, and the small ones are not in that list.

OpenStreetMap's [Nominatim](https://nominatim.org/) finds a place by name and returns its
administrative boundary. Tried on a Belgian village:
`/lookup?osm_ids=R<id>&format=jsonv2&polygon_geojson=1` returned a `boundary/administrative`
polygon of 114 points, with its bounding box and its full name (village, municipality,
province, country). `/search?q=<name>` gives the same for a typed name.

The public instance has a strict
[usage policy](https://operations.osmfoundation.org/policies/nominatim/), which this design
follows point by point:

- at most 1 request per second; an identifying User-Agent (not a library's default one);
- results cached on our side; repeated identical queries get blocked;
- **forbidden**: auto-complete, systematic queries (reverse geocoding a set of coordinates),
  scraping the `details.html` page, reselling results;
- end-user-triggered searches are fine for a moderate number of users; periodic requests are
  bulk geocoding;
- an app must let the user switch to another service without a software update;
- attribution shown; the data is ODbL (share-alike).

## Proposal

- **One direction only: a name typed by the user → an area.** Never reverse-geocode photo
  coordinates online: the policy forbids it, and it would send where the family was to a third
  party. Naming coordinates stays offline (GeoNames, 0030).
- **`places` page (0030)**: a "Search OpenStreetMap" button, used on click or Enter only (no
  auto-complete), typically when the offline search found nothing. The results are listed (full
  name, type); the chosen one is drawn on the map; the user names it (default: the OSM name)
  and saves it.
- **The Python server makes the request**, not the browser: User-Agent
  `media-hygiene/<version> (+https://github.com/cavo789/media-hygiene)`, one request per second
  at most (lock and monotonic clock), `format=jsonv2`, `polygon_geojson=1`,
  `polygon_threshold` to simplify the outline (around 50 m), `accept-language` from the locale.
  stdlib `urllib` in `asyncio.to_thread`: no new dependency. A short timeout and a clear message
  offline. The CSP of 0030 is unchanged: the browser only fetches map tiles.
- **Cached for good in `config.toml`**: the saved place holds its simplified outline and its OSM
  id (`osm = "R1234567"`, to refresh it on purpose). `classify` never calls the service: it
  works offline and is reproducible. `/config` holds `config.toml` only, never a side file.
- **A place is a circle or an area.** "Inside" is a point-in-polygon test (ray casting; holes
  and multipolygons handled), in `geo/areas.py`.
- **Service configurable**: `[geo] nominatim_url = "https://nominatim.openstreetmap.org"`, for a
  self-hosted instance or another provider; empty disables the online search.
- **Said on the page and in the documentation**:
  - only the text typed in the search box leaves the machine, never a photo or coordinates;
  - the attribution: "© OpenStreetMap contributors, ODbL";
  - a link to the usage policy and its limits.

## Acceptance

- [ ] Unit tests on recorded JSON responses, never the network: parsing, point in polygon
  (inside, outside, in a hole, multipolygon), two searches within a second are spaced out.
- [ ] `nominatim_url = ""` hides the button; offline, the page says so and the offline search
  still works.
- [ ] A place saved from an area survives a round trip through a commented `config.toml`
  (tomlkit) and matches the photos inside it, not those just outside its bounding box's corner.
- [ ] Documentation en + fr: policy link and limits, attribution, what leaves the machine; a
  fictitious place only (public repository); `.po` translated.
