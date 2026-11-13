# 0816 — WAL journal measured: a page read while an audit writes the index

- **Priority**: Medium
- **Batch**: page-speed
- **Depends**: —
- **Files**: `src/media_hygiene/index/repository.py`, `src/media_hygiene/index/read_only.py`, `tests/measure/pages/`, `tests/measure/pages-budget.md`

Follows PARTIAL 0807 (commit 59b6a913): a larger SQLite cache and a memory map gave at most
15 %, within noise, so nothing changed; WAL was left unmeasured. Decided by the maintainer in
the review of 2026-11-13 (`feedback-2026-11-13-3-iterate`): measure it.

## Context

The index runs in rollback-journal mode; an audit commits every 5 s
(`repository._COMMIT_EVERY_SECONDS`). A page of the home server read during an audit (the
home page launches audits) may wait on the writer's lock at each commit. WAL lets readers go on
while one process writes.

## Proposal

- Measure first, synthetic index at 100,000 files (`tests/measure/pages/library.py`), `nice -n 19`:
  a script runs an audit-like writer (the repository's own `put` + commit cadence) beside the
  pages bench; record each route's median and worst time, rollback journal vs `PRAGMA
  journal_mode = WAL` on the writer. Change nothing the figures do not justify (≥ 10 % on the
  median or a worst time cut by half).
- If kept: the `-wal`/`-shm` files beside the index are handled by `mh backup`, `shrink`, a
  restore, the read-only `?mode=ro` opens of a `:ro` cache mount (WAL needs the `-shm` file
  writable or `immutable=1`), Docker Desktop's file sharing of `/cache`, and the e2e tests.

## Acceptance

- [ ] The table (route × mode, median and worst, during an audit) in this TODO's status, *measured*
- [ ] WAL kept only on the figures; if kept, one test per file-handling path above
