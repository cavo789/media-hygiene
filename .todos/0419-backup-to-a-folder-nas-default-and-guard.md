# 0419 — `mh backup` / `mh restore`: `--to` / `--from` a folder, the NAS by default, a guard against a running `mh`

- **Priority**: Medium
- **Batch**: launcher
- **Depends**: —
- **Files**: `src/media_hygiene/cli/templates/mh.ps1.j2`, `src/media_hygiene/cli/templates/mh.sh.j2`, `src/media_hygiene/cli/templates/mh_backup.ps1.j2`, `src/media_hygiene/cli/templates/mh_backup.sh.j2`, `src/media_hygiene/cli/templates/mh_guards.ps1.j2`, `src/media_hygiene/cli/cmd_backup.py`, `src/media_hygiene/services/cache_backup.py`, `src/media_hygiene/services/cache_restore.py`, `tests/e2e/`, `documentation/en/commands/backup.md`, `documentation/fr/commands/backup.md`

## Why

Leftovers of 0352, decided by the maintainer (inbox, 2026-10-27): the index must survive the
loss of the PC, so the archive goes on the NAS when there is one.

## What

1. `--to <folder>` / `--from <folder>` (USB stick, NAS): `mh.ps1` mounts that folder for the run
   (removable drives via `_removable`).
2. Default: `<push target>\.mh-backups` when `push-target.txt` exists (the NAS), else the mh home
   as today.
3. Guard: refuse while another `mh` container runs (`docker ps` with a label every `mh` container
   carries, in `mh_guards.*`).
4. The rows of files moved by `sort` / `undo` / quarantine between backup and restore (`tags`,
   `descriptions`, `faces`; the restored index lacks the `moves` rows written since): check with
   the `cache-invalidation-reviewer` agent, one test per event.
5. An e2e test on a real Docker volume (`docker volume rm`, then `mh restore`).
