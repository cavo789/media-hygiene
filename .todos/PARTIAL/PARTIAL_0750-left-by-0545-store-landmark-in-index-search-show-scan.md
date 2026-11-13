# 0750 — What 0545 left: Keep each photo's landmark and town in the index: searchable, shown, scanned once

- **Priority**: Medium
- **Batch**: backlog
- **Depends**: —
- **Files**: `.todos/DONE/0545-store-landmark-in-index-search-show-scan.md`

Split from section 0545 of PARTIAL 0718 (`.todos/PARTIAL/PARTIAL_0718-code-left-in-partial-todos.md`), as decided by the maintainer in the review of 2026-11-12 (one TODO per remaining section). Source TODO: `.todos/DONE/0545-store-landmark-in-index-search-show-scan.md`.

## Left (as listed in 0718; the source TODO has the full wording)

- `classify` still computes its towns: a trip's town is the largest town around a group's centre, and `folder_town` comes from the folder's name; neither is a fact of one photo, and reading the stored town would change the folders of existing sorts.
- The GPS line of the large view (`search/gps_town.py`), `album_reader`, `tags/place_words` still use the gazetteer.
- The other tile pages (import, quarantine, phone, reviews) show no place.
- The `{region}` placeholder of `[classify] layout` is kept although the regions are "never in folder names".
- The landmark and the town are computed once and stored; the slideshow and classify no longer recompute them
- Search finds a photo by its landmark or its town; tiles and large view show it
- A scan fills it for the existing GPS photos, offline; tests for moves/renames

## How to proceed

- Check each item against the code first: some may be done already and only unticked (then say so and close them).
- File follow-ups for what is really left; every figure says *measured* or *estimated*; a new limit: say whether it should be a setting.
- Documentation EN + FR and French strings when something user-facing changes.

## Status — PARTIAL (2026-11-13)

### Done
- The GPS line of the large view names the stored place (the tile's label, `spot_labels`)
  instead of asking the gazetteer again; the snapshot stays the fallback for a photo with no
  row yet (`search/hits.py`, `search/exif_facts.py`; test `tests/unit/test_gps_town.py`).
- Checked: landmark and town are stored and filled offline by the audit/`spots`, search finds
  them, tiles and large view show them (0545): those three acceptance lines hold.

### Not done
- `classify`'s towns (trip = largest town around a group's centre, `folder_town` from the
  folder's name) and the `{region}` placeholder of `[classify] layout`.
  **Reason:** reading the stored town would change the folders of existing sorts, and removing
  `{region}` breaks a layout the user wrote: a maintainer decision, not guessed.
- `album_reader` and `tags/place_words` still use the gazetteer.
  **Reason:** scope of this lot; same move as the GPS line (read `spots_by_key`).
- Import, quarantine, phone and review tile pages show no place.
  **Reason:** their files are mostly not in the index; needs a lookup by path or digest first.
