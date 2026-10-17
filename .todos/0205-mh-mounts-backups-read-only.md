# 0205 — `mh`: a backup folder, always mounted read-only, `clean` included

- **Priority**: Medium
- **Batch**: launcher
- **Depends**: 0204
- **Files**: `src/media_hygiene/cli/cmd_launcher.py`, `src/media_hygiene/services/launcher.py`, `src/media_hygiene/services/launcher_folders.py`, `src/media_hygiene/services/launcher_kept.py`, `src/media_hygiene/services/launcher_update.py`, `src/media_hygiene/cli/templates/mh.ps1.j2`, `src/media_hygiene/cli/templates/mh.sh.j2`, `src/media_hygiene/cli/templates/mh_folders.ps1.j2`, `src/media_hygiene/cli/templates/mh_folders.sh.j2`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/unit/test_launcher_folders.py`, `tests/unit/test_launcher_rewrite.py`, `documentation/en/commands/launcher.md`, `documentation/fr/commands/launcher.md`, `documentation/en/start/03-several-folders.md`, `documentation/fr/start/03-several-folders.md`, `tests/measure/mh-measure.ps1`
- **Needs maintainer**: after the work, one run on Windows: `launcher --backup` on another drive, `mh audit` then `mh clean`: the backup mounted `:ro` both times (Docker refuses any write), its two results shown

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
- Windows (maintainer): the run above.

## Gain (estimated)

A backup checked without any risk of change, whatever command `mh` runs; no `docker run` to
write by hand.
