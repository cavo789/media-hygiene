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
