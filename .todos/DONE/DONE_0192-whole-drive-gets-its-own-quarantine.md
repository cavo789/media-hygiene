# 0192 — A whole drive as photo folder (`E:\`) gets its own quarantine, `E:\media-hygiene` excluded

- **Priority**: Medium
- **Batch**: quarantine-drives
- **Depends**: —
- **Files**: `src/media_hygiene/services/launcher_drives.py`, `src/media_hygiene/services/launcher.py`, `src/media_hygiene/cli/templates/mh.ps1.j2`, `src/media_hygiene/cli/templates/mh.sh.j2`, `documentation/en/commands/launcher.md`, `documentation/fr/commands/launcher.md`, `tests/unit/test_quarantine_drives.py`

## Why

Decided at the review of the 2026-10-16 run (question 10, about 0183): today a drive whose
photo folder holds its quarantine folder (`E:\` itself) gets none (`_holds` in
`launcher_drives.py`): the quarantine would be read as photos, so its files go to `C:`, the
very copy across drives 0183 removed. The maintainer wants `E:\media-hygiene\quarantine` for it
too, with `E:\media-hygiene` left out of the scan.

## What

- `with_drive_quarantines`: no longer skip a drive whose photo folder holds the quarantine.
- The scan must never read `<drive>\media-hygiene` (quarantine, and whatever the tool writes
  there later): find how `mh` can pass an exclusion for that run only (an `excluded` entry, an
  env var, a launcher-written `--exclude`: to check what exists), without writing into the
  user's `config.toml`. The walker already skips the quarantine mount points? To check:
  the folder is reached here through `/data/e/...`, not through `/quarantine/e`.
- Tests: `E:\` as photos → `/quarantine/e` mounted, the audit of a tree holding
  `media-hygiene/quarantine/<run>/x.jpg` does not list `x.jpg`; a later `clean` moves to
  `E:`, `undo` brings back. Same for WSL `/mnt/e`.
- Docs EN/FR: the launcher page sentence that says such a drive falls back to `C:`.
