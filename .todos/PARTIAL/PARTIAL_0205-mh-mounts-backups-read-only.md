# 0205 — `mh`: a backup folder, always mounted read-only, `clean` included

- **Priority**: Medium
- **Batch**: launcher
- **Depends**: 0204
- **Files**: `src/media_hygiene/cli/cmd_launcher.py`, `src/media_hygiene/services/launcher.py`, `src/media_hygiene/services/launcher_folders.py`, `src/media_hygiene/services/launcher_kept.py`, `src/media_hygiene/services/launcher_update.py`, `src/media_hygiene/cli/templates/mh.ps1.j2`, `src/media_hygiene/cli/templates/mh.sh.j2`, `src/media_hygiene/cli/templates/mh_folders.ps1.j2`, `src/media_hygiene/cli/templates/mh_folders.sh.j2`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/unit/test_launcher_folders.py`, `tests/unit/test_launcher_rewrite.py`, `documentation/en/commands/launcher.md`, `documentation/fr/commands/launcher.md`, `documentation/en/start/03-several-folders.md`, `documentation/fr/start/03-several-folders.md`, `tests/measure/mh-measure.ps1`

## Context

Chosen by the maintainer on 2026-10-17 (proposal F2, the `mh` part). 0204 adds the backup role to
the tool. A backup must never be written, whatever the command: `mh` mounts the photo folders
read-write for the acting commands (`clean`, `sort`, …), so a backup needs its own mounts, always
`:ro` — the operating system then forbids any change, as for an audit.

## What to do

- `launcher --backup "E:\Backup"` (repeatable), `mh folders add --backup <folder>` and
  `mh folders remove <folder>`: the folder is mounted with `:ro` for every command, `clean`
  included, and given to the tool as `--backup`; `mh folders` lists the backups apart ("Compared,
  never changed:").
- The rewrite of `mh` (0176) keeps them, as it keeps the photo folders.
- `cmd_launcher.py` is at 192/200: the new option's plumbing goes to `launcher_folders.py` or a new
  module.
- Step 11 of `mh-measure.ps1`: `mh folders add --backup <work folder>`, `mh clean` refused to write
  there (a file planted in the backup stays), the two results in the summary.

## Explicit non-goals

- Copying what is missing (the user copies).
- A dialog for `--backup` (0201 covers `folders add` without a folder; a backup can use it later).

## Acceptance

- Unit: the rendered scripts (both shells) mount a backup with `:ro` for the acting commands too,
  pass `--backup`, list it apart; ASCII; the rewrite keeps it.
- Docs both languages: launcher page, step 3.
- Windows (maintainer, after the work; closes the TODO, implementing needs no maintainer — inbox 2026-10-19): one run on Windows: `launcher --backup` on another drive, `mh audit` then `mh clean`: the backup mounted `:ro` both times (Docker refuses any write), its two results shown.

## Gain (estimated)

A backup checked without any risk of change, whatever command `mh` runs; no `docker run` to
write by hand.

## Status — PARTIAL (2026-10-19)

### Done
- `launcher --backup "E:\Backup"` (repeatable; `cli/cmd_launcher_parts.py`, which also took
  `_commands` out of `cmd_launcher.py`, 192 → 167 lines) and `services/launcher_backups.py`: a
  backup that is, holds or lies in a photo folder or another backup is refused (stopping script).
- Both scripts mount each backup `-v host:point:ro` for every command, `clean` included (not
  `${mode}`), check it is there before each run, and append `--backup` (`E:\Backup` in mh.ps1, the
  mount point in mh.sh) to the commands whose options hold `--backup` (read from the CLI itself:
  audit, clean, crosscheck, review).
- `mh folders add --backup <folder>`, `mh folders remove <folder>` (either list); `mh folders` lists
  them apart ("Your backups, compared, never changed:"); the rewrite and `mh update` give them back
  as `--backup`; removing the last photo folder is still refused with backups.
- Tests: `test_launcher_folders.py` (PowerShell text, ASCII, refusals, bash run: `:ro` mount for
  clean and history, `--backup` only for clean, a backup not plugged in stops), `test_launcher_rewrite.py`
  (bash: add --backup, list, rewrite keeps it, remove). French translated.
- Docs both languages: launcher page (options table, what mh does, `mh folders`), step 3 (`mh folders
  add --backup` instead of `mh audit --backup`, which mounted nothing), clean step 5's example too.
- Step 11 of `mh-measure.ps1` extended (11h/11i: on `-OtherDrive` when given; its mount line, the
  audit's two lines, the files left after `mh clean --yes`, a write refused by Docker in a `:ro` mount).

### Not done
- The Windows run (maintainer): image built from branch `iterate/2026-10-19`, then
  ```powershell
  cd C:\temp
  Invoke-WebRequest https://raw.githubusercontent.com/cavo789/media-hygiene/iterate/2026-10-19/tests/measure/mh-measure.ps1 -OutFile .\mh-measure.ps1
  Unblock-File .\mh-measure.ps1
  .\mh-measure.ps1 -Only 11 -Count 20 -OtherDrive E:
  ```
  **Reason:** needs Windows + Docker Desktop.
- Stale capture: the built-in help of `launcher` in `documentation/{en,fr}/commands/launcher.md`
  (new `--backup` option): `docs_screenshots` (TODO 0244).
