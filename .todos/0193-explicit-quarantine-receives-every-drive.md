# 0193 — An explicit `--quarantine` receives the files of every drive

- **Priority**: Medium
- **Batch**: quarantine-drives
- **Depends**: —
- **Files**: `src/media_hygiene/services/launcher_drives.py`, `documentation/en/commands/launcher.md`, `documentation/fr/commands/launcher.md`, `tests/unit/test_quarantine_drives.py`

## Why

Decided at the review of the 2026-10-16 run (question 11, about 0183): with
`launcher --quarantine D:\Q`, the photos of `C:` now get `C:\media-hygiene\quarantine`
(`own` is `D:` in `with_drive_quarantines`, so every other drive, `C:` included, gets its
own). A quarantine the user named is where they want the files: it receives every drive's.

## What

- `with_drive_quarantines`: when the quarantine is not the default one (`--quarantine` given),
  add no drive quarantine at all; the default (`$HOME\media-hygiene\quarantine`) keeps the
  per-drive routing.
- `mh folders add` writes `mh` again with `--quarantine` kept (`launcher_kept.py` does):
  check it stays explicit.
- `clean`'s line about another drive (0182) then tells the user the copy crosses drives: it
  is their choice, said, not refused unless short of room.
- Tests: `--quarantine D:\Q` with photos on `C:` and `E:` → no `/quarantine/<x>` mount;
  default → `/quarantine/e` as today. Docs EN/FR: the sentence on `--quarantine`.
