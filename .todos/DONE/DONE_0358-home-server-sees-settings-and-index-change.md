# 0358 — The home server sees its settings and the index change, and follows them by itself

- **Priority**: High
- **Batch**: home
- **Depends**: 0355
- **Files**: `src/media_hygiene/config/`, `src/media_hygiene/services/runtime.py`, `src/media_hygiene/cli/context.py`, `src/media_hygiene/search/fts.py`, `src/media_hygiene/search/meaning_index.py`, `src/media_hygiene/search/folders.py`, `src/media_hygiene/index/read_only.py`, `src/media_hygiene/services/home.py`, `tests/`

## Context

Phase 3 of the single server (maintainer, 2026-10-24: "it could be detected by code, and reloaded
automatically"). Today each page reads `config.toml`, `/config/people/*.toml` and the index when its
container starts, then never again: it lives a few minutes. The home server lives the whole
session, while the user edits `config.toml`, saves a place or a name on a page, or runs `tags`,
`audit`, `clean` as steps in their own containers (0355). Without this TODO it would show stale
settings and stale results.

## What to do

1. **Settings read again when their files change**: before each request (or at most once a
   second), the content of `config.toml` and of each people file compared with what was loaded
   (a digest of the bytes, a few KB: not the mtime, which a copy can keep); changed → the
   settings rebuilt (file < env < CLI layers as today) and every holder of the old settings given
   the new ones (a settings provider instead of the frozen `Settings` captured at start). A file
   that no longer parses: the last good settings kept, one line on the page saying why.
2. **The index changed by another container**: `PRAGMA data_version` (free) checked by every cache
   built from the index — the full-text table (done), the folder tree, the names of the people
   (0354's thread started again), the meaning vectors, the home page's state.
3. **Locks**: the index is in rollback-journal mode; a reader during another container's commit
   can meet `database is locked`. A `busy_timeout` on every read-only connection, short read
   transactions; the same point is in 0353 (writes every 2.7 s during `tags`).
4. **One test per event** (`.claude/rules/workflow.md`): `config.toml` saved atomically (new
   inode), edited in place, copied keeping its mtime, deleted, made unparsable; a people file
   added, renamed, removed; the index written by another connection (tags, a clean's prune);
   a reader holding a read lock while another commits.
5. Measure the cost per request of the checks on the maintainer's PC (a step of
   `mh-measure.ps1`: Docker Desktop's file sharing made `stat` slow before, 0277).

## Acceptance

- A setting changed in `config.toml` while the home page is open shows at the next click, without
  restarting anything; a `tags` run in the window of mh shows in search at the next search.

## Gain

No stale page in a session of hours (correctness); no restart of `mh` after a settings change.

## Status — PARTIAL (2026-10-24)

### Done
- `services/fresh_runtime.py`: `FreshRuntime` compares a SHA-256 of `config.toml` and every
  file of `/config/people/` (names and bytes) at most once a second (`CHECK_SECONDS`); changed
  → `load_settings` again, a new `Runtime` (`dataclasses.replace`); a file that no longer loads
  keeps the last good settings, said once in the console (not tried again until it changes).
  Used by the home page's state (`cmd_home`) and by the search app of the home server
  (`SearchHere`: built again on new settings; no index yet: tried again at each request).
- The names of the people (`search/names_soon.py`, `NamesKept`): read again in a thread when
  a digest of the index's `faces` (rowid, path, number) and `moves` changes — a `sort` moves a
  face's path in place (`UPDATE OR REPLACE`, `index/schema.py`), so counts alone would miss it;
  checked only when `PRAGMA data_version` changed; the searches meanwhile keep the names they
  had (waited for only the first time).
- Already fresh, read in the code: the full-text table and the meaning vectors
  (`data_version`), the folder tree (read at each request, no cache).
- Locks: `sqlite3.connect` waits 5 s on a lock by default (`connect_read_only` keeps it), so a
  reader meets `database is locked` only after 5 s; no setting added.
- Tests, one per event: atomic save, edit in place, copy keeping the mtime, removal, a file
  that no longer loads, a people file added/renamed/removed, once a second
  (`test_fresh_runtime.py`); names read again on a move, never waited for after the first, a
  face moved changes the mark (`test_search_meaning.py`); the app built again
  (`test_home_pages.py`).

### Not done
- The home page's own audit (`page_audit`) keeps the settings of the start.
  **Reason:** its settings (exclusions, workers) are read when it starts; rarely changed
  during a session — to do with 0357 if the maintainer asks.
- *A file that no longer loads* is said in the console of the server, which runs in the
  background since 0355 (docker logs): the page does not say it yet.
  **Reason:** needs a field in the home page's state and its line on the page; small, left
  for 0357 with the people/places pages, which are the ones writing these files.
- The cost per request on Windows (a step of `mh-measure.ps1`).
  **Reason:** Docker Desktop's file sharing only on the maintainer's PC.

## Inbox (2026-10-27)

- `page_audit` settings and the page's line for a file that no longer loads → moved into 0417; the Windows cost per request stays a measure. Closed to DONE (maintainer, 2026-10-27).
