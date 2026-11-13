# 0807 — SQLite reads of the pages use the PC's RAM: cache and memory map measured

- **Priority**: High
- **Batch**: page-speed
- **Depends**: —
- **Files**: `src/media_hygiene/index/read_only.py`, `src/media_hygiene/index/repository.py`, `src/media_hygiene/index/schema.py`, `src/media_hygiene/search/fts.py`, `tests/measure/pages-budget.md`

Filed by the speed review of 2026-11-13. **Measure first; no product change until the
figures are in this TODO** (as 0794).

## Context

Every connection to the index (`FactsRepository.open`, `connect_read_only`,
`SearchIndex.open`) runs with SQLite's defaults: a 2 MB page cache per connection
(`cache_size = -2000`), no memory map, rollback journal. The index of a 52,000-file
library with faces and metadata is tens of MB (*estimated*; `du` of
`media-hygiene-cache` to confirm), so the heavier routes of the pages-budget table
(*search: a period* 120 ms warm at 100,000, *events: a year* 109 ms, *home state*
73 ms, *found events* 1.8 s) read pages from the OS cache through SQLite's small cache
at every request. The maintainer's PC has 64 GB: the whole index fits in memory many
times over.

## Proposal

- Measure on the synthetic index at 100,000 and 300,000 (`tests/measure/pages/bench`),
  one variant at a time, `nice -n 19`: (a) defaults; (b) `PRAGMA cache_size = -262144`
  (256 MB) on the read-only connections of the pages; (c) `PRAGMA mmap_size` at the index
  file's size (read-only connections only: a memory map and a writer in another process
  are fine in SQLite, but say so in the docstring); (d) `PRAGMA journal_mode = WAL` for
  the writer during an audit (readers of the home page no longer wait on the writer's
  commits every 5 s): measure a page route during a running audit, before/after.
- Keep what the figures justify; a bound that depends on the machine's RAM would be a
  named constant first (`few-settings`), a `[cache]` setting only if a small machine (a
  NAS, a laptop) needs less.

## Acceptance

- [ ] The table of (a)–(d) at 100,000 and 300,000 in this TODO's status, *measured*
- [ ] Nothing changed that the figures do not justify (a variant under 10 % gain is dropped
      and said so)
- [ ] WAL, if kept: the `.wal`/`.shm` files beside the index are handled by `mh backup`,
      `shrink`, the read-only `?mode=ro` opens of a `:ro` cache mount, and the e2e tests
