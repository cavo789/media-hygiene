# 0618 — The day set on a group counts for late files, found folders and the event folder

- **Priority**: Medium
- **Batch**: search
- **Depends**: 0597 (DONE)
- **Files**: `src/media_hygiene/classify/`, `src/media_hygiene/services/`

## Why

Review of 0597: `late_files`, `found_folders` and `event_folder` still read `media_date` only; an undated photo dated by hand on the Library is not a late file nor counted in a found folder's days.

## What

Read the `.xmp` sidecar day there too, below EXIF and video, as `classify` already does. Measure the extra cost of reading sidecars on those scans first (skill `measure-before-ranking`); moves of the file or its sidecar keep one test each.

## Done when

A hand-dated photo counts in the three (tests); cost measured and stated.

## Done (2026-11-06)

`classify/hand_days.py`: the search's temporary `sidecar_days` table is read beside
`media_date` by `late_files`, `found_folders` and `event_folder` (own date wins, the hand
day at noon). `search.sidecar_days.read_days_again` refreshes it at each ask of the late
files and found folders pages. Tests: `tests/unit/test_hand_dated_events.py` (the three,
file + sidecar moved, sidecar alone moved, own date wins). Cost measured (synthetic
index of 50 000 dated rows, in memory, warm disk): 14 ms per ask; with 2 000 undated files
in 100 folders, 1 000 sidecars: 145 ms per ask.
