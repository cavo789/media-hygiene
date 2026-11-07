# 0649 — Type the landmark a photo shows in the large view of search/browse

- **Priority**: medium
- **Batch**: unassigned
- **Depends**: 0489
- **Files**: src/media_hygiene/tags/xmp_places.py, src/media_hygiene/index/spot_rows.py, src/media_hygiene/search/, src/media_hygiene/review/templates/pick_large.html.j2, documentation/en/, documentation/fr/

## Context

Decided in 0489 (2026-10-31, 2026-11-02). *Measured* (0489, maintainer's index, read-only):
GeoNames names a monument within 200 m for only 9.6 % of the 281 located photos (19.9 %
within 500 m, 22.4 % within 1 km): the name is typed by hand far more often than confirmed.

## What to do

- In the large view of search/browse (skill `photo-picking-pages`, `pick_large`): a key and a
  field *📍 Landmark…* proposing the GeoNames landmarks within 500 m (nearest first, with
  their distance), the OSM name if one was fetched, and a free field; *Wrong name* rejects the
  current one.
- Written into the XMP sidecar (`Iptc4xmpExt:LocationShown/Sublocation`, the truth, other
  tools read it, survives moves; same ownership rule as `xmp_places`), cached in `spots` with
  source `user` (already kept by `spot_fill` / `spot_namer`). A sidecar's name wins over the
  index at the next audit (index rebuilt: read back from XMP).
- A rejected name stored (`rejected`, like `people/`) and never proposed again, at the next
  show or scan.
- Confirmed → offered as a place (`[[classify.places]]`, circle around the landmark, 0551) so
  the other photos of the spot get it — offered, never silent.
- Shown as a 📍 chip beside the tags (tile, large view), searchable; slideshow corner.
- Save read back from disk and shown; bilingual docs; `i18n_update`.

## Acceptance

- [ ] Typed, suggested, rejected names work from the large view, saved in XMP and index
- [ ] Rejected names never proposed again; tests for a moved photo (sort, undo, Explorer rename)
- [ ] Docs EN/FR, captures listed for `docs_screenshots`

## Done (2026-11-07)

Key L in the large view of `library`, `POST /api/landmark` (`search/landmark_desk.py`): proposals within 500 m with distances, OSM name, free field, *Wrong name*; sidecar `LocationShown/Sublocation` + `mh:landmarksRejected` (`tags/xmp_landmark.py`), journaled via `XmpService`, read back; `spots` source `user` (`index/spot_user.py`); rows rebuilt from the sidecar, rejected names dropped (`services/spot_sidecars.py`). Tests: `tests/integration/tags/test_landmark_sidecars.py`. Docs `commands/spots.md`, `commands/library.md` EN/FR.

## Left

- [ ] Confirmed → offered as a place (`[[classify.places]]`, circle around the landmark, 0551), offered, never silent
- [ ] 📍 chip beside the tags (tile, large view), searchable; slideshow corner
- [ ] `mh undo` of a landmark run refreshes the `spots` row (today stays `user` until the next change of stamp/position)
- [ ] Headless Chromium check of the dialog (skill `photo-picking-pages`); `docs_screenshots`
