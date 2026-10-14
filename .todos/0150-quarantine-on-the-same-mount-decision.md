# 0150 — Decision: a quarantine on the photos' own mount, so that setting a file aside is a rename

- **Priority**: Medium — every file `clean` sets aside is copied today (≈ 43 MB/s through Docker Desktop), and needs as much free space on the quarantine's drive; a change of the mount design, for the maintainer to decide
- **Batch**: mounts
- **Depends**: —
- **Files**: `src/media_hygiene/actions/journaled.py`, `src/media_hygiene/actions/quarantine.py`, `src/media_hygiene/actions/purge.py`, `src/media_hygiene/paths/`, `src/media_hygiene/scan/walker.py`, `src/media_hygiene/services/launcher.py`, `documentation/en/clean/`, `documentation/fr/clean/`
- **Needs maintainer**: a decision on the mount design (quarantine beside the photos or not), after a measurement on Windows

## Context

Speed and cache review of 2026-10-14 (third pass). `/quarantine` is a mount point of its own
(`-v "$HOME\media-hygiene\quarantine:/quarantine"`, added by `mh`). Linux refuses `rename` and
`link` between two mount points, even two folders of one disk (`rename(2)`: `EXDEV`, "rename()
does not work across different mount points, even if the same filesystem is mounted on both").
So `move_no_replace` copies every file set aside: exclusive copy, `fsync`, the copy read again
to prove it, then the original removed. 0138 kept that on purpose for moves between mounts.

Measured by the maintainer for 0138: 420 files (3.0 GB) in ≈ 70 s through that copy, ≈ 43 MB/s
of file size. With 90,000 copies of 2.8 MB (30 % of 300,000 photos) that is about 1.6 hours for
the moves alone, on top of the byte comparisons (0149). The quarantine also needs as much free
space as everything set aside, on the drive of `$HOME` (usually `C:`), whatever drive the photos
are on. On the photos' own mount, a move is a rename, or a link then an unlink on Docker
Desktop's NTFS mounts (0138): instant, no space used.

## Options

1. **Keep the design** (one `/quarantine` mount): simple to explain, one place for every drive,
   nothing new in the user's photo folders. Costs time and space as above.
2. **A quarantine beside the photos**: `<mounted folder>/.media-hygiene-quarantine/<run>/…` (name
   to choose). Moves become renames. What it changes, and loses:
   - a new folder appears inside the user's photo folder, visible in Explorer (a leading dot
     hides nothing on Windows);
   - the walk must skip it (as album folders are skipped by their marker); `purge`, `undo`,
     `history`, `status` and the reports find a run's files on several mounts (the journal
     already records every target path);
   - the guides drop the `/quarantine` mount (`mh`, the README, every `clean` page, en + fr),
     and the memory note on the mount design changes;
   - a protected or read-only folder cannot hold it (`clean` already refuses `:ro` mounts).
3. **Both**: `/quarantine` stays the default; a setting (`[clean] quarantine = "beside"`) opts
   in to option 2 for large collections. More code paths to test.

## What to do

1. Measure first: a `clean` of a few thousand copies on a Windows test folder with today's
   image, time per GB for the moves, and the same with `--delete` (no move). This gives the
   share of the moves in a clean, after 0149.
2. The maintainer chooses an option (list of trade-offs above).
3. If option 2 or 3: a follow-up TODO with the design (folder name, walk, purge, undo, docs).

## Acceptance

- The decision and the measured figures written here; the follow-up TODO filed if needed.
