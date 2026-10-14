# 0138 — Move by hard link where `renameat2` is refused (Docker Desktop NTFS)

- **Priority**: High — every `sort`, `undo` and quarantine move on Windows copies the bytes today
- **Batch**: actions
- **Depends**: —
- **Files**: `src/media_hygiene/actions/no_overwrite.py`, `tests/unit/test_no_overwrite.py`, `documentation/en/commands/sort.md`, `documentation/fr/commands/sort.md`, `documentation/en/sort/07-sort.md`, `documentation/fr/sort/07-sort.md`

## Context

Measured by the maintainer on 2026-10-14 (TODO 0056, Part 4, item 0057), image 0.3.0, Docker
Desktop on Windows, one bind mount of an NTFS folder (`C:\Temp\sort-test`):

- `renameat2(AT_FDCWD, a, AT_FDCWD, b, RENAME_NOREPLACE)` → `EINVAL`, so `move_no_replace`
  falls back to `copy_then_remove`: a `sort` of 420 files (3.0 GB) inside that one mount took
  ~70 s, its `undo` 1 min 01 s. On the whole collection that is hours, and needs free space
  for the largest file in flight.
- On the same mount, `os.link(a, c)` then `os.unlink(a)` works and keeps the inode
  (11258999068581133 before and after); plain `os.rename` works too (but replaces silently).
- TODO 0041 already proved hard links are true NTFS links through Docker Desktop, both with a
  `C:\…` and a WSL `/mnt/c/…` mount.

`link()` fails with `EEXIST` when the target exists: like `RENAME_NOREPLACE`, the refusal is the
act itself, so the no-overwrite guarantee of `no_overwrite.py` holds.

## Change

In `move_no_replace`: `renameat2(RENAME_NOREPLACE)` → on `COPY_INSTEAD` errors other than
`EXDEV`, try `os.link(source, target)` then `os.unlink(source)` → on `EXDEV`, `EPERM`,
`ENOTSUP`/`EOPNOTSUPP`, `ENOSYS` from `link` (as `actions/album_links.py` classifies them),
`copy_then_remove` as today. `EXDEV` from `renameat2` goes straight to the copy (a link cannot
cross mounts either).

- `FileExistsError` from `link` propagates unchanged (nothing changed, as today).
- A crash between `link` and `unlink` leaves two names for the same inode. The resume of
  `sort` and `undo` must treat "target exists and `os.path.samefile(source, target)`" as the
  move done, then drop the source name; check `actions/journaled.py` and
  `actions/restore.py` (both call `move_no_replace`) and add that case where a pending move is
  replayed.
- Do not add a `[sort]` setting: the fallback order is automatic.

## Docs (en + fr)

`commands/sort.md` says "On one disk, a move is a rename: nothing is copied, no space is used";
`sort/07-sort.md` says "On the same disk, a file is renamed: instant". Once this lands they stay
true (a link + unlink is instant and uses no space); until then they are wrong under Docker
Desktop. Check the wording still matches after the change (renamed or linked: instant).

## Tests

Unit tests with a fake renamer raising `EINVAL`: the link path is taken (same inode, source
gone); `link` raising `EEXIST` → `FileExistsError`, source intact; `link` raising `EPERM` → copy;
`renameat2` raising `EXDEV` → copy, `link` not called; the half-done state (both names, same
inode) is completed on replay.

## Explicit NON-goals

- No change to cross-mount moves (two `-v`): they keep the verified copy.
- No change to `album` (already hard links).

## Acceptance

- On a Docker Desktop NTFS mount, the maintainer's `sort` of a test folder keeps the inodes and
  takes seconds, not a minute; `undo` likewise.
- Targeted tests pass; `lint` clean.

## Status — DONE (2026-10-14)

### Done
- `move_no_replace`: `renameat2(RENAME_NOREPLACE)`; on a refusal other than `EXDEV`
  (`EINVAL`, `ENOSYS`, `ENOTSUP`), `os.link` then `unlink` of the source
  (`actions/link_move.py`); `EXDEV`/`EPERM`/`ENOTSUP`/`EOPNOTSUPP`/`ENOSYS` from `link` → the
  verified copy as before; `EEXIST` from `link` → `FileExistsError`, nothing changed.
- Half-done state: a `FileExistsError` whose target is the very same file (`samefile`) is a
  move killed between link and unlink: the old name is removed and the move counts as done.
  This sits in `move_no_replace` itself, so every caller (`journaled.py` quarantine moves,
  `sort`, `restore.py` for `undo`) completes it when the move is replayed or run again.
- Tests: `tests/unit/test_link_move.py`. Docs `sort/07` en + fr: a precision for Docker
  Desktop (the wording "renamed: instant" stays true).

### Not done
- The maintainer's measurement on a Docker Desktop NTFS mount (inodes kept, `sort`/`undo` in
  seconds). **Reason:** needs Windows + Docker Desktop and an image build.

## Inbox (2026-10-14)

- The measurement is now step 7 (classify, sort, undo of the test folder) of `tests/measure/mh-measure.ps1`.

## Windows measurement (2026-10-14) — not conclusive

Measured by the maintainer on 2026-10-14 with `tests/measure/mh-measure.ps1` (Windows, Docker
Desktop, image built from `main`; run `measures-20261014-2133`, test folder of 2,000 photos
copied twice). `sort --yes` of the default proposal over 4,001 files (2.7 GB), one NTFS mount: 2 min
01 s (Duration), 153.5 s wall time; `undo` of that sort: 52 s. That is ≈ 30 ms per file, more
than the sequential copies of an `undo` after `clean --delete` (≈ 18 ms per file, same run) and
6× `clean --delete` (≈ 5 ms per file, 4 at a time): either `sort` copies, or each move is
latency-bound (*estimate*, from these ratios; not checked). The run did not record which:
`mh-measure.ps1` step 7 now compares the NTFS file ids before and after the sort (kept id =
renamed or linked), and `-Only 7` runs that step alone.

## Windows measurement with file ids (2026-10-14) — `sort` copied every file; fixed

`mh-measure.ps1 -Only 7` (run `measures-20261014-2145`, 4,000 files, 2.7 GB, one NTFS mount):
`sort` 1 min 59 s, **0 of 4,000 files kept their NTFS id, 4,000 new ids: copied**; its `undo`
51 s. Cause: `sort` never reached the link of this TODO. `Relocator.move`
(`actions/sort_moves.py`) has its own `rename_no_replace` call and went from `EINVAL` straight
to `copy_then_remove` (after a full read for the journaled SHA-256); only `journaled.py` and
`restore.py` call `move_no_replace`. Fixed: `sort_moves._linked` tries `moved_by_link` before
the copy (`EXDEV` still copies at once); tests in `tests/integration/test_sort_moves.py`
(EINVAL → same inode, no digest; EINVAL + EPERM → copied and proven; a name taken → suffix,
nothing replaced). Not handled in `sort`: a run killed between link and unlink leaves two names
of one file (the resumed row reports its target as taken). To close: rebuild the image, rerun
`-Only 7` (step 7c now also checks the ids after the undo), expect every id kept and `sort` in
seconds.

## Undo after a sort by link, and the closing measurement (2026-10-14)

With `sort` linking, its `undo` failed on every file: `[Errno 1] Operation not permitted`.
`mh-measure.ps1` step 8 (each operation alone, Docker Desktop NTFS mount) showed `renameat2`
→ `EINVAL`, and `link`, `unlink`, `rmdir`, `mkdir` all working; `utime` with explicit times →
`EPERM` on a file made by Windows (seen as owner 0; the image runs as uid 1000) and fine on a
file the tool made. `restore.perform` set the time back after every restore: harmless while
`sort` copied (the copies were the tool's), refused once the files kept their identity. Fixed:
`perform` sets the time only when it changed (a file moved back kept it; a copy already got it
from `copystat`). Test: `test_undo_of_a_move_by_link_never_sets_the_time_again`.

Measured by the maintainer (`measures-20261014-2203`, `-Only 7,8`, 4,000 files, 2.7 GB):

| | before (copies) | after (links) |
|---|---|---|
| `sort` | 1 min 59 s, 4,000 new NTFS ids | 51 s, 4,000 of 4,000 ids kept (−57 %) |
| `undo` of that sort | 51 s | 37 s, no failure, 4,000 of 4,000 back with their first id (−27 %) |

Both still go one file at a time (≈ 13 ms and 9 ms per file): see 0161. The raw error text of
the failed run: 0162. The half-done state (killed between link and unlink in `sort`) stays as
noted above.
