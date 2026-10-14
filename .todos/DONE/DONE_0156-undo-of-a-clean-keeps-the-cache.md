# 0156 — `undo` of a `clean` gets back what the cache knew; `purge` forgets it

- **Priority**: Low — the cache is correct today (`clean` forgets what it removes); this only spares the work of checking, describing and analysing the faces of restored files again
- **Batch**: index
- **Depends**: 0146
- **Files**: `src/media_hygiene/services/clean.py`, `src/media_hygiene/services/undo.py`, `src/media_hygiene/cli/cmd_purge.py`, `src/media_hygiene/actions/purge.py`, `src/media_hygiene/index/schema.py`, `src/media_hygiene/index/repository.py`, `documentation/en/start/02-keep-the-cache.md`, `documentation/fr/start/02-keep-the-cache.md`, `tests/integration/`

## Context

Speed and cache review of 2026-10-14 (third pass). The maintainer asked that `clean` and
`purge` keep the cache correct by themselves. They do:

- `CleanService._forget_removed` removes from the index every file the run set aside or deleted
  (every table: facts, descriptions, tags, faces, measures);
- `purge` erases quarantine folders, which the index never held.

What is lost: `undo` restores the files, and `_follow_moves_back` moves their rows from the
quarantine path back to the original path, but there is no row at the quarantine path any more.
The restored files are checked again from zero by the next audit, and their descriptions, tags,
faces and colours are gone. Undoing a clean of 50,000 copies means decoding 50,000 photos again,
and redoing any model work done on them.

## What to do

1. `clean` parks the rows of each file it moves to the quarantine instead of deleting them: a
   `parked` table (quarantine path, run, the rows of every table in one JSON document), so that
   no reader of the index (inventory, `tags`, `search`, `places`, `people`, `status`) has to
   learn to skip quarantined files. Deleted files (`--delete`, empty files) are forgotten as
   today.
2. `undo` puts the parked rows back at the original path, with the `moves` record of 0146 so
   that the names confirmed in `people` follow. A move by rename or link keeps size and mtime;
   a copy keeps the mtime (`copystat`). A row whose file changed since reads as stale, as usual.
3. `purge` removes the parked rows of the runs it erases.
4. Docs en + fr (`start/02-keep-the-cache.md`): `undo` gives back what the cache knew of the
   restored files.

## Acceptance

- Integration test: audit, clean, undo, audit: no picture decoded again (counting fake), the
  faces and descriptions back at their paths; after clean then purge, no parked row is left.
- An index of the previous schema upgrades with an empty `parked` table.
