# 0339 — Places: the map opens framed on every place the photos were taken

- **Priority**: Medium
- **Batch**: places
- **Depends**: —
- **Files**: `src/media_hygiene/places/templates/places.html.j2`, `src/media_hygiene/places/board_state.py`, `tests/integration/test_places_command.py`

## Context

Asked by the maintainer (2026-10-24): on arrival, the map should show at once the whole area
where the photos were taken — photos in France, Belgium and Italy: the three countries on screen,
a marker on each place.

## Today (read in the code, not measured on the maintainer's map)

The page already calls `map.fitBounds(...)` once `GET state` answers
(`places.html.j2`, end of the script), on the GPS clusters and the saved places, `maxZoom:
NAMED_ZOOM` (16). The maintainer does not see that framing, so something defeats it — to find
first, likely candidates:

- an outlier stretches the box to the whole world: a cluster at `0, 0` (a camera writing an
  empty GPS as zeros) or a wrong hemisphere;
- the folders placed by hand (`GET folders`, loaded after) are not in the box;
- the drawer / left column hides part of the map: the other `fitBounds` call of the page passes
  `paddingBottomRight: [hidden(), 0]`, this one does not;
- the map's size is read before the layout settles (`map.invalidateSize()` before fitting).

## To do

1. Reproduce with the demo tree plus synthetic clusters in three countries and one at `0, 0`.
2. Frame on the clusters, the places and the folders placed (`📌`), the box padded for the
   column; points at exactly `0, 0` left out of the box (still drawn).
3. A "Show everything" button (or key) brings that framing back after zooming in.

## Acceptance

- [ ] Clusters in three countries: on arrival, the three are on screen, none hidden by the column.
- [ ] A `0, 0` cluster does not zoom the map out to the world.
- [ ] Docs `commands/places.md` (en + fr) say it; `docs_screenshots` to run (the capture changes).
