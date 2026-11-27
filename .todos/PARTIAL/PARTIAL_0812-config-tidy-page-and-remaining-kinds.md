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

## Status — PARTIAL (2026-11-27)

### Done
- Town renames: a `[classify.town_names]` key the offline gazetteer does not know is listed
  by `config tidy` (ticked) and removed by `--apply` (`tidy_find._town_names`, table keys in
  `tidy_write`; `LibraryFacts.towns`, the gazetteer read only when renames exist). Tests in
  `tests/unit/test_config_tidy.py`; docs EN + FR (`commands/config.md` table); French string.
- `place_photos` relocation checked: 0570's `photo_refs_audit` already rewrites the `path`
  of a moved photo found by content after each audit; only the removal of lines found
  nowhere is left.

### Not done
- The web page with ticks (visible rows only, Apply now, way back home, read back).
  **Reason:** out of this lot's size; needs a new served page under the pages contract.
- `place_photos` lines whose content is found nowhere: removal from `places/<name>.toml`
  (not `config.toml`: `tidy_write` edits config.toml only). **Reason:** a second writer.
- `people`: a linked file that is missing makes the settings fail to load
  (`people_files.linked_section` raises), so `tidy` can never run to list it; a file linked
  by nobody needs a file move, not a config edit. **Reason:** question for the maintainer:
  should a missing person file load as an empty list (then tidy offers to unlink it)?
- `docs_screenshots`: the `config` page's console blocks are unchanged (no new output line).
