# 0569 — `mh backup`: a copy on the PC too, allowed while a page runs

- **Priority**: Medium
- **Batch**: backup
- **Depends**: —
- **Files**: `src/media_hygiene/cli/cmd_backup.py`, `src/media_hygiene/services/backup_archive.py`, `src/media_hygiene/services/launcher_backups.py`, `src/media_hygiene/cli/templates/mh*.ps1.j2`, `documentation/en/`, `documentation/fr/`

## Why

Questions of 0414 **sauvegarde dans .mh-backups du NAS** and 0419 **--to/--from, garde-fou**
(review of `feedback-2026-10-27-iterate.md`, 2026-11-02). Maintainer: keep both copies (PC and
NAS), so a restore works with the NAS off. Allow `backup` (read-only, SQLite backup API) while a
page runs; only `restore` is refused.

## What

- First check what the code does today for both points; only the missing part is done.
- `backup` writes the archive on the PC (under the `mh` home, kept files only) and on the NAS
  target. `restore` lists both, newest first.
- The "a page is running" guard applies to `restore` only. Test: backup during an open page
  gives a consistent archive.
- Docs en + fr.
