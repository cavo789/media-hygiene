# 0232 — `places`: a cluster of videos says "1 photo", then "0 photos out of 1"

- **Priority**: High — the page contradicts itself
- **Batch**: places
- **Depends**: —
- **Files**: `src/media_hygiene/places/clusters.py`, `src/media_hygiene/places/board.py`, `src/media_hygiene/places/templates/places.html.j2`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/unit/test_places_clusters.py`, `documentation/en/commands/places.md`, `documentation/fr/commands/places.md`

## Seen

Maintainer, 2026-10-17 (`mh places`, screenshot): a cluster line reads **1 photo**; clicking it
opens a panel titled **0 photos sur 1**.

## Cause (read in the code, not reproduced)

- `clusters_of` (`places/clusters.py`) counts **every** located file in `count`, videos
  included, but keeps only pictures in `members` (`_SHOWN = {IMAGE, RAW}`: a video has no
  preview).
- The page labels `count` with `T.photos` ("{n} photo(s)"), so a cluster holding one video says
  "1 photo"; `showPhotos` then finds `shown = 0 < count = 1` and writes
  `T.somePhotos` = "{shown} photos out of {count}".
- `somePhotos` is a plain `_()`, not `ngettext`: "0 photos sur 1" / "1 photos sur 3" are
  wrong in French and English alike.

## To do

1. `Cluster` counts pictures and videos apart (`pictures`, `videos`); the state sends both.
2. The cluster button and the map tooltip name what is there: "1 vidéo", "3 photos, 1 vidéo".
3. The panel: the videos are listed by name (and folder, see 0233), with a 🎞 mark instead of a
   preview; its title says "Les 3 photos et la vidéo de ce groupe" or "Les 24 premières photos
   sur 40" — `ngettext` for every count, never "0 photo".
4. A cluster of videos only still opens its panel (the names: often enough to recognise it).
5. Tests: a cluster of one video, of pictures and videos, of more pictures than
   `MEMBERS_KEPT`; the French plural forms.
6. `i18n_update`; docs EN + FR if a capture shows the count; `docs_screenshots` to run.
