# 0786 — An HEVC video the browser cannot play shows its frame in the large view

- **Priority**: Low
- **Batch**: videos
- **Depends**: —
- **Files**: `src/media_hygiene/share/templates/album.js.j2`, `src/media_hygiene/search/templates/`, `src/media_hygiene/review/templates/pick_*`

Left by 0733 (from 0373). An iPhone HEVC `.MOV` plays in Edge only with the HEVC extension
installed (not checked on the maintainer's PC). Since 0733 every video has a frame thumbnail
(`/thumb/<key>.jpg`, decoded once and cached): when `<video>` fires `error` in a large view
(album viewer, the shared `pick_*` large view), show that frame (`/preview/<key>.jpg`) with the
format said, instead of a black box. Wire it with `addEventListener` (the pages' CSP has no
inline handlers), in the shared large view so every tile page gets it.

## Needs maintainer

- Whether Edge on the maintainer's PC plays a real iPhone HEVC `.MOV` (a step in
  `tests/measure/mh-measure.ps1` can open it); the fallback is worth it either way.
