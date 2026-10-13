# 0130 — Reuse an up-to-date index instead of walking every file again (terabyte collections)

- **Priority**: High — every `classify` run pays the full walk; users may have terabytes of photos
- **Batch**: scan
- **Depends**: —
- **Files**: `src/media_hygiene/scan/walker.py`, `src/media_hygiene/services/classify.py`, `src/media_hygiene/services/audit.py`, `src/media_hygiene/index/schema.py`, `src/media_hygiene/index/listing.py`, `src/media_hygiene/index/pruning.py`, `src/media_hygiene/console/`, `documentation/en/start/02-keep-the-cache.md`, `documentation/fr/start/02-keep-the-cache.md`

## Context

Review of the 2026-10-13 run. `mh classify --no-describe` on the maintainer's collection
(`C:\Photos`, ~70,000 files, Docker Desktop) took long although the model part only mapped 49
cached descriptions (seconds). `ClassifyService._inputs` (`services/classify.py`) always walks
every root (`scan/walker.walk`: `os.scandir` + a `stat` per file, across the Windows share), then
looks each file up in the index by (path, size, mtime) and runs the integrity check, which reads
the cache. The cache saves the decoding, never the walk. `tags` and `inventory` read the index
alone (instant) but do not see files added since the last audit.

Decided with the maintainer: **reuse the cache whenever it exists and is up to date; do
everything to avoid wasting time**, since a user may have terabytes of photos.

## What to do

1. **Measure first** on the real collection (read-only mount, see the maintainer's notes): time
   of the listing, of the index lookups, of the integrity pass, of events + rules, for `audit`
   and `classify`, warm and cold. Record the figures here; the design follows the biggest share.
2. **Directory-level freshness** (the likely winner): at each walk, keep in the index every
   walked folder with its mtime (and entry count). The next walk `stat`s the folders only; a
   folder whose mtime did not change takes its file list from the index (no `scandir`, no
   per-file `stat`); a changed folder is listed as today. Check on Docker Desktop (Windows share
   / 9p), WSL ext4 and native Linux that adding, removing and renaming a file changes its folder's
   mtime.
3. Known gap to decide with numbers: a file rewritten **in place** (same name) does not change
   its folder's mtime. Options: accept it with a periodic full check (`audit --full`, or every Nth
   run / after N days, said in one line), or keep a per-file `stat` for photo folders only when it
   is cheap. Never silently trust a stale entry for `clean` (it byte-compares before deleting
   anyway) — the reuse is for `audit`, `classify`, `status`.
4. Say it in the console, in one line (the pedagogy rule): "Index of 2026-10-13 reused for 412
   unchanged folders; 3 folders read again." and a 💡 for the full check.
5. Docs en + fr (`start/02-keep-the-cache.md`): what the cache saves now (the walk too), and how
   to force a full check.

## Explicit NON-goals

- Watching the file system (inotify / USN journal): not reachable from a container.
- Changing the content digests or the integrity rules themselves.

## Acceptance

- Measured before/after on the real collection: a second `classify` with nothing changed no
  longer lists every file (the figures in this TODO's status).
- Tests: an added, a removed and a renamed file are seen; an unchanged folder is not listed; the
  full check reads everything.
