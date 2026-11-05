# 0469 — Evaluate: could search replace `places`?

- **Priority**: Low
- **Batch**: search
- **Depends**: —
- **Files**: `src/media_hygiene/cli/cmd_places.py`

## Why

The maintainer, 2026-10-29: search is the central page; every other page it could absorb is one
less to learn. Evaluate before implementing.

## What

Candidate: places map: a place filter in search (map picker). List what `places` does that search does not (features, keys, data written), the
cost to add each to search, and what users lose. Recommend keep / absorb; no code change here.

## Decided (2026-11-05, maintainer, start of /todo:iterate)

Run the evaluation unattended and write it into this TODO, with its recommendation (keep / absorb).
The keep/absorb decision stays the maintainer's, asked on the pull request; no code change, no page
removed.

## Evaluation (2026-11-05, unattended; read from `commands/places.md`, `places/` and `search/place_*`, 4 023 lines counted by `wc -l`, costs estimated)

`library` already has: the Place filter, *📍 Place…* on the photos picked (0553), the offer of the
same day and folder (0554), `place:` words.

| What `places` does that `library` does not | Cost to add to library (estimated) |
|---|---|
| The Leaflet map, its clusters of about 200 m, and their drawer of photos | High: a second main view in a tile page, its CSP for the tile host, its own left column |
| Draw a place: click, radius slider, drag; `[[classify.places]]` written with comments kept | Medium to high: the form and the map, the save code reused |
| Find a town offline; OpenStreetMap outlines (`osm`, opt-in, position-free search) | Low once the map is there |
| Folders named after a town, *To place* / *Placed*, *Any folder*: `[[places.folders]]`, *Not a town* | Medium: a list unrelated to photos picked, which `xmp_folder_gps` reads |
| *Set this cluster aside* and Restore | Low, but only meaningful on the map |
| The switch of reverse lookup (`[places] reverse_lookup`) | Low; a setting rather than a search feature |
| Keys: N / P along a folder list, Enter saves, Esc steps back | Low; they clash with the photo grid's (I, arrows), so a separate mode |

**Users lose if absorbed**: nothing if the map is carried over whole, but then the page has two
models (tiles to pick, a map to draw on), against "one layout, one way to pick"; a person drawing a
place has no photos picked. Without the map, they lose drawing a place, the only way to create one.

**Recommendation: keep `places`**, already hidden from `mh --help` (`PAGE_ONLY`) and served by the
home server. What `library` can absorb it already has: choosing and filling a place. Perhaps add a
link *Draw a new place* in the *📍 Place…* dialog (cost: a line, proposed, not done). Decision: the
maintainer's.

## Decided (2026-11-05, review of feedback-2026-11-05-iterate)

Keep the page (maintainer). For `slideshow`: the verb is hidden from `mh --help`, still callable.
