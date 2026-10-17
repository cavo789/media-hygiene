# 0233 — `places`: one photo drawer over the map, for a cluster and for a folder, grouped by folder

- **Priority**: High — the maintainer missed the panel twice
- **Batch**: places
- **Depends**: 0232
- **Files**: `src/media_hygiene/places/board.py`, `src/media_hygiene/places/folders.py`, `src/media_hygiene/places/templates/places.html.j2`, `src/media_hygiene/paths/host_paths.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/integration/test_places_photos.py`, `tests/integration/test_places_folders.py`, `documentation/en/commands/places.md`, `documentation/fr/commands/places.md`

## Seen

Maintainer, 2026-10-17 (`mh places`, screenshots), twice the same trap:

1. "It took me several seconds to understand the button. I clicked and nothing happened…" The
   **N photos** button of a cluster opens its grid at the bottom of the "largest clusters" list
   (`<section id="photos">` after `<ul id="clusters">`): with 13 lines and the side column
   scrolled, out of sight.
2. "I got caught again": a click on a line of "Folders named after a town" opens its photos and
   the **Not a town** / **Save this position** buttons at the bottom of that list
   (`<section id="folderPanel">` after `<ul id="folders">`, 53 lines): "not practical at all".

The maintainer expected the photos **and their path**: thumbnails alone hide the folder name,
which often names the place or the event ("2014-07 Mariage Julie", "Geer").

## Design

Both panels are the same thing (some photos, a few actions) and fail the same way: they live at
the end of a list of variable length. One **drawer** replaces both, at a fixed place: over the
right side of the map (full height, about 40 % of the width; full width under 700 px), never in
the left column.

- Header: what is shown ("Douarnenez — 37 photos without GPS", "Cluster — 11 photos, 1 video"),
  then the actions **at the top**, before any photo: for a cluster **Name this place**, ✕ set
  aside (0234), Add to a place (0237 if decided); for a folder **Save this position**, **Forget
  its position**, **Not a town**; ✕ closes (Esc too).
- Body: the photos grouped by folder, one heading per folder with its **host path**
  (`C:\Photos\2014\Geer`, `HostPaths.to_host`; the last folder name in bold), its thumbnails
  under it, the largest folder first. `GET /api/cluster/<rank>` and `GET /api/folder/<rank>` send
  `folder` (host path) per photo.
- The map stays visible on the left of the drawer: the folder's pin stays draggable, hovering a
  thumbnail still pins where it was taken; the map pans so that the point is not under the drawer.
- The clicked line stays highlighted in its list; another line replaces the drawer's content.

## To do

1. The drawer (one `<section>`, one render function fed by either source), the two old panels
   removed.
2. The cluster button says what it does: "🖼 11 photos", tooltip "Show its photos".
3. A click on a thumbnail opens it larger inside the drawer (the file's full host path and name
   under it, ←/→ through the photos, Esc back to the grid); the preview pool renders a larger
   edge for it, cached like the grid's.
4. Tests: the folder grouping and host paths (a photo of `/data/c/…`, of a second drive); a photo
   moved since the audit (`found: false`) keeps its place; the folder actions still read back
   from `config.toml`.
5. `i18n_update`; docs EN + FR (`commands/places.md`: where the photos open); `docs_screenshots`
   to run.

## Decided (2026-10-17)

- The maintainer chose the drawer over the map, not a separate page.
