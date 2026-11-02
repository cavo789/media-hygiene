# 0561 — The index recovers by itself after a crash: no "readonly database" on the pages

- **Priority**: High
- **Batch**: index
- **Depends**: —
- **Files**: `src/media_hygiene/index/read_only.py`, `src/media_hygiene/services/search.py`, `src/media_hygiene/services/data_checks.py`, `src/media_hygiene/services/home_pages.py`, `tests/integration/test_index_after_crash.py`
- **Needs maintainer**: a confirmation on Windows that a `-journal` file sat next to `C:\…\cache\index.sqlite` after a crash (only if it happens again)

## What happened (2026-11-01)

Windows crashed while `mh` was running. At the next start, the home page's **Retrouver**
gave a 404; once the page said why (fixed the same day), it read:

> The index /cache/index.sqlite cannot be read: attempt to write a readonly database.

`mh audit` fixed it, without deleting anything.

## Likely cause (to confirm, not measured)

The index uses SQLite's default rollback journal. A crash in the middle of a write leaves a
*hot journal* (`index.sqlite-journal`) next to the file. The next connection must roll it
back before reading — which is a write. The search (and every reader through
`connect_read_only`, `?mode=ro`, or `MeaningIndex.open`) opens the file read-only, so SQLite
refuses: "attempt to write a readonly database". The audit opens it read-write, rolls the
journal back, and everything works again. This matches what was seen; it was not reproduced
on the maintainer's machine.

Every Windows crash, power cut or Docker Desktop kill during an audit, an import or a
`tags` run can leave the index in this state, and each read-only page then refuses to open.

## What to do

1. Reproduce in a test: write in a transaction, copy the file **and** its `-journal` while it
   is open (or kill a child process mid-write), then open it with `connect_read_only` and
   `open_search`: the error must show up.
2. When a read-only open fails with `SQLITE_READONLY` (or a `-journal` / `-wal` file is
   present) and the cache is writable: open the index read-write once, which rolls the hot
   journal back, close it, then open read-only again. Say one line in the console
   ("mh was interrupted last time: the index was put back in order"), never on silent success.
3. A `:ro` cache mount (rare): keep the refusal, with the `mh audit` command (already shown
   since 2026-11-01).
4. The same path for every reader of `unreadable_index` (inventory, places, xmp, albums,
   classify_people): one helper in `index/read_only.py`, not six fixes.
5. Consider `PRAGMA journal_mode=WAL` for writers (recovery by readers is easier, readers no
   longer blocked by an audit): check first that WAL works on Docker Desktop's Windows bind
   mounts (to check — WAL needs shared memory, which some network/9p filesystems refuse).

## Where the user gains

Before: after any crash, Retrouver / Browse / Events / places refuse to open until the user
runs `mh audit` by hand (they must understand the message). After: the page opens at the
first click, with no action from the user (estimated: one rollback of a journal costs
milliseconds; no file is read again).
