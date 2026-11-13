# 0812 — Tidy config.toml: the page with ticks, place photos, town renames, people files

- **Priority**: Medium
- **Batch**: backlog
- **Depends**: —
- **Files**: `src/media_hygiene/config/tidy_find.py`, `src/media_hygiene/services/config_tidy.py`, `src/media_hygiene/review/` (new page), `src/media_hygiene/cli/menu_catalog_*.py`, `documentation/en|fr/commands/config.md`

What 0751 (from 0550) left. `mh config tidy` and its service already list and remove the
stale entries (backup, tomlkit, read back); the path rules aimed at roots never indexed are
left alone (0751).

## Wanted

- A web page listing the stale entries with ticks (opt-in ones unticked), applying only the
  ticked rows shown, backup + read back from disk, *Apply now* placement and the way back home
  (memory: visible in web or nonexistent; seeing first; never act on hidden). Reuse the shared
  page frame and list components.
- `[[classify.place_photos]]` line by line: a path gone whose `sha256` (+ `size`) is indexed
  elsewhere → path updated (check what 0570's relocation after each audit already covers
  first); else the line removed, the block with its last line.
- Town renames whose GeoNames name is unknown (a typo).
- `people`: a `/config/people/<name>.toml` linked but missing, or one linked by nobody.

## Acceptance

- [ ] One test per kind; the page applies only the visible ticked rows; save read back.
- [ ] Docs EN + FR, French strings, menu catalog; `docs_screenshots` flagged stale.
