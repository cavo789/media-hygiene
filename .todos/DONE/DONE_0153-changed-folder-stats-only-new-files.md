# 0153 — A folder that changed: `stat` only its new files, and the files of a big folder in parallel

- **Priority**: Medium — one `stat` costs ≈ 1 ms through the Windows share; a flat folder of 100,000 photos (phone dumps, exports, a synced photo library) is listed again in full, ≈ 107 s, at every audit after one photo is added
- **Batch**: scan
- **Depends**: —
- **Files**: `src/media_hygiene/scan/walker.py`, `src/media_hygiene/scan/folder_cache.py`, `src/media_hygiene/scan/folder_entries.py`, `src/media_hygiene/services/listing.py`, `tests/unit/test_folder_reuse.py`, `documentation/en/start/02-keep-the-cache.md`, `documentation/fr/start/02-keep-the-cache.md`

## Context

Speed and cache review of 2026-10-14 (third pass). Since 0130 a folder whose modification time
did not change is taken from the index (one `stat` of the folder). A folder that changed is
read again in full: `os.scandir`, then `snapshot` `stat`s every file of it, one after the other,
in one thread. Folders are read 16 at a time (`Sizes.IO_CONCURRENCY`), the files inside one
folder are not.

Measured on 2026-10-14 through WSL's `/mnt/c` (the 9p sharing Docker Desktop also uses for
`C:\` folders), real photos of `C:\Photos`, cold:

| `stat` of 1,000 files | per file (wall) |
|---|---|
| one at a time | 1,070 µs |
| 4 in flight | 141 µs |
| 16 in flight | 99 µs |

For `C:\Photos` itself (1,017 folders, the largest of 4,097 files, half of the files in the
51 largest folders) today's 16 folders at a time is already as good as it gets: ≈ 4 s for a cold
listing, simulated from the measures. Collections shaped otherwise pay much more:

- a flat folder (phone dumps, exports, a photo library synced by a cloud client: check which ones):
  100,000 files ≈ 107 s per listing, in one thread;
- and since adding, removing or renaming one photo changes the folder's time, such a folder is
  listed in full at every audit while it keeps growing (a sync client adds photos every day).

A file rewritten in place does not change its folder's time: its `stat` is trusted until the
listing is `[scan] full_check_days` old (7 days), or `audit --full`. Keeping the stats of the
unchanged names of a changed folder trusts nothing more than that.

## What to do

1. A changed folder whose last listing is younger than `full_check_days`: `scandir` it, keep
   the cached `stat` of each name already listed (same name, same kind), and `stat` only the
   names that are new. Removed names disappear with the new listing. `audit --full` and
   listings older than `full_check_days` still `stat` everything.
2. The `stat`s of one folder (new names, or every name when it must be read in full) run in
   parallel: batches handed to threads within the same I/O limit as the folders, so that a
   folder of 100,000 files no longer runs in one thread. The order of the entries stays the
   one of today (sorted afterwards).
3. The console line of 0130 stays true ("… unchanged folders taken from the index, … read");
   docs en + fr (`start/02-keep-the-cache.md`): a folder where photos were added is read again,
   but only the new photos are examined one by one.

## Acceptance

- Unit tests (`test_folder_reuse.py`): a changed folder `stat`s only its new names (counting
  fake); a renamed file is seen; a file rewritten in place is still found by `audit --full`.
- A walk of a synthetic folder of 20,000 files on a slow fake `stat` (e.g. 1 ms) takes about a
  sixteenth of the time of one thread.
