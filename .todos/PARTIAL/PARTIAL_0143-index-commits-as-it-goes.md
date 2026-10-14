# 0143 — The index commits as it goes: a killed first audit keeps the hours already spent

- **Priority**: Medium — a first audit of 70,000 files runs for a long time; today all of its work is lost if the container is killed, and the next run starts again from zero
- **Batch**: index
- **Depends**: —
- **Files**: `src/media_hygiene/index/repository.py`, `src/media_hygiene/services/audit.py`, `src/media_hygiene/__main__.py`, `tests/integration/`

## Context

Speed review of 2026-10-14 (second pass). `FactsRepository` opens one SQLite connection and
commits **once**, in `__exit__`. Every `put` of an audit stays in one open transaction until the
command ends. That is fine when the command ends normally, or on Ctrl+C (`KeyboardInterrupt`
reaches `__exit__`). It loses everything when the process is killed:

- `docker stop`, or closing the PowerShell window: Docker sends `SIGTERM` to PID 1, which is
  `media-hygiene` (the `ENTRYPOINT`, no `--init`). PID 1 ignores a signal it has no handler
  for, so after 10 s Docker sends `SIGKILL`. Nothing is committed.
- The maintainer's PC crashes under heavy load (memory "low machine load"). A crash in the
  middle of a first audit is a realistic case, not a corner case.

The next audit then decodes, probes and hashes every file again. With the cache, a killed run
should cost only the files not yet stored.

## What to do

1. `FactsRepository`: commit every N seconds (e.g. 5 s), from `put`, measuring time with
   `time.monotonic()`. Keep the final commit in `__exit__`. A commit every few seconds costs
   nothing next to decoding photos.
2. `PRAGMA journal_mode = WAL` and `PRAGMA synchronous = NORMAL` on open: commits become
   cheap appends, and readers (a `status` run during an audit) are not blocked. Check that WAL
   works on the `/cache` named volume and on a Windows bind mount (`-v C:\…:/cache`): WAL needs
   shared memory, so on a bind mount through Docker Desktop it may fail. In that case, keep
   the default journal on such mounts (detect it with the mount table, as `MountKind` does)
   and say so in a comment.
3. `SIGTERM`: install a handler in `main()` that raises `KeyboardInterrupt` (or a dedicated
   exception handled like it), so `docker stop` ends a command like Ctrl+C does: commit,
   journal closed, workers stopped, exit code 130/143. Check `clean` and `sort` (journals)
   behave as on Ctrl+C.
4. Docs en + fr (`start/02-keep-the-cache.md`): an interrupted audit keeps what it already
   checked; the next one continues.

## Acceptance

- Integration test: an audit killed with `SIGKILL` halfway (subprocess) leaves an index with
  the files done before the last commit; the next audit decodes only the others (counting
  fake).
- `docker stop` of a running audit exits within 10 s, with the index committed (e2e).
- No slowdown of a full audit on the demo tree (measured).

## Status — PARTIAL (2026-10-14)

### Done
- `FactsRepository.put` commits when 5 s passed since the last commit (`_COMMIT_EVERY_SECONDS`);
  the final commit stays in `__exit__`. `mark_walked` / `walked_at` moved to `index/walks.py`
  (functions taking the repository) to keep `repository.py` under 200 lines.
- `__main__.main` installs a SIGTERM handler raising `KeyboardInterrupt`: `docker stop` ends a
  command like Ctrl+C (index committed, journal closed, exit 130).
- Tests `tests/unit/test_index_commits.py`: commits after the interval (another connection
  sees the rows), a subprocess killed with SIGKILL keeps its committed rows, SIGTERM → Ctrl+C.
- Docs `start/02-keep-the-cache` en + fr.

### Not done
- WAL / `synchronous = NORMAL` (item 2). **Reason:** WAL needs shared memory that a Docker
  Desktop bind mount may not offer, and it cannot be checked here (no Windows); a commit every
  5 s with the default journal costs nothing next to decoding photos.
- The e2e check that `docker stop` of a running audit exits within 10 s with the index
  committed, and the measure on the demo tree. **Reason:** needs an image build (kept for the
  maintainer: low machine load).
