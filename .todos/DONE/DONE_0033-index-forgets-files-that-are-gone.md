# 0033 — The index forgets the files that are gone (deleted by `clean`, moved or deleted by hand)

- **Priority**: Medium — harmless for deduplication today, wrong data for every reader of the index tomorrow
- **Batch**: scan
- **Depends**: —
- **Files**: `src/media_hygiene/scan/walker.py`, `src/media_hygiene/index/repository.py`, `src/media_hygiene/index/schema.py`, `src/media_hygiene/services/audit.py`, `src/media_hygiene/services/clean.py`, `documentation/en/02-keep-the-cache.md`, `documentation/fr/02-keep-the-cache.md`

## Context

The index (`/cache/index.sqlite`) is keyed by container path. `FactsRepository` only reads and
upserts: no row is ever removed. A row stays forever when its file is:
- deleted or quarantined by `clean`;
- deleted, renamed or moved by hand (the new path gets a new row, the old one stays).

Today it only costs disk space: the audit asks the index about the files the walk found, never
about the others. It becomes wrong data as soon as something reads the index **without a
walk**:
- the inventory export (0032) would list files that no longer exist;
- the map of 0030 would draw clusters of deleted photos.

Checking every row with a `stat` at export time would be a scan: the audit is the moment that
knows which files exist, and `clean` knows which ones it removed.

## Proposal

- **Audit prunes.** After the walk, rows under a walked root whose path the walk did not
  list are deleted, in one statement (temporary table of seen paths, or `executemany`): fast on
  70,000 rows. Never pruned, because absence proves nothing there:
  - rows outside the roots of this run (another disk, audited another day);
  - rows under a folder the walk could not read, or a file it could not `stat`: `walk` must
    return these (today it only logs them), so a disk that hiccups does not wipe its facts;
  - rows under an `excluded` folder (not walked);
  - with `--ext`, rows whose extension is out of scope.
- **`clean` forgets** the rows of the files it deleted or moved to the quarantine, from its
  outcome, so the index is right before the next audit. `undo` does nothing: the restored
  files are hashed again at the next audit, as new files.
- **Last complete walk per root**: a small `roots` table (root path, date of the last walk that
  listed it fully). The export of 0032 says it ("C:\Photos: audited on …").
- Next schema version; `prepare` creates the table on an older index. If 0025 lands first,
  take the version after its own.
- The number of forgotten rows goes to the log (`--verbose`), not the console summary.
- In-memory index (no persistent `/cache`): nothing to do.

## Acceptance

- [ ] A file deleted between two audits loses its row; a file renamed keeps one row, under its
      new path.
- [ ] Rows are kept for: another root not mounted this time, an unreadable folder, a file whose
      `stat` fails, an excluded folder, an extension out of `--ext` (one test each, fakes for
      the unreadable cases: tests may run as root).
- [ ] After `clean`, the rows of deleted and quarantined files are gone; after `undo`, the next
      audit indexes the restored files again.
- [ ] An index of the previous version upgrades in place and keeps its rows.
- [ ] Documentation en + fr (02-keep-the-cache: the cache forgets what disappeared).
