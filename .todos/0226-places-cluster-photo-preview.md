# 0226 — `places`: click "11 photos" to see the photos of an unnamed cluster

- **Priority**: Medium
- **Batch**: places
- **Depends**: —
- **Files**: `src/media_hygiene/places/clusters.py`, `src/media_hygiene/places/board.py`, `src/media_hygiene/places/app.py`, `src/media_hygiene/places/templates/places.html.j2`, `src/media_hygiene/cli/cmd_places.py`, `documentation/en/commands/places.md`, `documentation/fr/commands/places.md`
- **Needs maintainer**: a decision: mount the photo folders (read-only) for `places`, or show only the previews already in the cache

## Wish

Maintainer, 2026-10-17, on `mh places` ("Les plus grands groupes sans nom" list,
"11 photos — Nommer ce lieu"): a click on *11 photos* shows the photos of that cluster, to
recognise the place before naming it.

## Today

- `places/clusters.py`: a cluster keeps only its middle and its count. The module docstring
  says so on purpose: "Only counts and cell middles reach the page." The paths are dropped
  when the cells are counted.
- `cli/cmd_places.py` needs only `/config` and `/cache`. The photo folders (`/data`) are not
  mounted, so the original files cannot be read.

## To do

1. Keep the members of each cell, in container paths: at least the first N, and a setting if
   N should vary. Proposal: 24 photos, shown in a grid of thumbnails under the list or over the
   map. Keep the "the largest first" order of the list.
2. A route `GET /api/cluster/<id>` that returns the paths' preview keys, and a `/preview/<key>`
   route, served like `review` (loopback `Host` only; same `views.preview_key`, so a file that
   changed gets a new key).
3. Where the pictures come from (the decision):
   - **A.** `places` mounts `/data` read-only (`:ro`) and builds the previews like `review`
     does (`/cache` previews, `[cache] previews_max_gb`). `mh places` must then pass the photo
     folders (to check in `mh.ps1.j2`/`mh.sh.j2`).
   - **B.** Show only the previews the cache already holds (from earlier reports or reviews),
     with a placeholder for the others. Nothing new to mount, but the result is often incomplete.
   Proposal: A, with the mounts read-only (🔒) as for `audit`.
4. Also worth doing: hovering a thumbnail shows its marker on the map, and a click centres the
   map on the cluster (already done when the line is clicked? to check).
5. Tests: the route refuses an unknown cluster or key; a file renamed since the index was built
   is missing, not an error (see `.claude/rules/workflow.md`, anything stored by path).
6. Documentation EN + FR (`commands/places.md`, the sort guide's places step); `i18n_update`;
   then run `docs_screenshots`.
