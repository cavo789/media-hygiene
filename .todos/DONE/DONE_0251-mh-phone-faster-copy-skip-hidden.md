# 0251 — `mh phone`: check a copy at once instead of after 200 ms, and skip the phone's hidden files

- **Priority**: Medium
- **Batch**: launcher
- **Depends**: 0219
- **Files**: `src/media_hygiene/services/launcher_phone.py`, `src/media_hygiene/cli/templates/mh_phone.ps1.j2`, `src/media_hygiene/services/phone_plan.py`, `tests/unit/test_launcher_phone.py`, `tests/unit/test_phone_plan.py`, `documentation/en/commands/launcher.md`, `documentation/fr/commands/launcher.md`

## Context

Measured by the maintainer on 2026-10-19 (step 19 of `mh-measure.ps1`, Samsung A72, Windows
PowerShell 5.1; see 0219's Status):

- The first `mh phone` copied 801 files (3.13 GB) in 317.2 s: **10.2 MB/s**, where large videos
  came at 29.5 MB/s and 20 photos copied by the measure (no wait between them) at 24.4 MB/s.
- `_phone_wait` sleeps `POLL_MILLISECONDS` (200) **before** its first look, then needs one more
  look to see the length stop changing. At 24 MB/s the copying itself is ≈ 131 s (*estimated*:
  3.13 GB / 24.4 MB/s); the ≈ 186 s left are ≈ 0.23 s per file (*estimated*), about one or two
  poll periods each.
- A file `.temp-20240906_105433899_20.mp4` was copied: a hidden temporary file of the phone (a
  name starting with `.`), not a photo of the user.

## What to do

1. Look at the staged copy **before** the first sleep, and poll faster (e.g. 25 ms) for the first
   second, then 200 ms (a large video does not need fast polling). Keep the "length = size and
   opens exclusively" proof and the stall limit unchanged.
2. `phone_plan`: skip a file whose name starts with `.` (counted apart: "hidden files of the phone
   left out: N", like the lines skipped today), so it is neither copied nor listed as new.
3. Tests: the rendered wait looks before sleeping; a `.temp-…` line is left out and counted.

## Acceptance

- Unit tests above; `tests_quick`; commit gate.
- The maintainer's next step 19 run: the first `mh phone` above 20 MB/s on the same phone
  (*expected*, from 24.4 MB/s without waits), no `.temp-` file in the copies.

## Gain (estimated)

An import of 801 files: 317 s → ≈ 150 s (−50 %, *estimated* from the 0.23 s per file above);
a family's phone of 5,000 photos: ≈ 19 min less waiting at the first import.
