# 0414 — `mh backup` writes to `<push target>\.mh-backups` when `mh push` has a target

- **Priority**: Low
- **Batch**: launcher
- **Depends**: —
- **Files**: `src/media_hygiene/cli/templates/mh.ps1.j2`, `src/media_hygiene/cli/templates/mh.sh.j2`, `src/media_hygiene/services/launcher_push.py`, `tests/unit/test_launcher*.py`, `documentation/en/commands/backup.md`, `documentation/fr/commands/backup.md`

## Context

0352 (commit 49bc59d, PARTIAL) mounts `$HOME\media-hygiene\backups` on `/backups`. Decided by the
maintainer in the review of 2026-10-27: when `mh push` has a target (`push-target.txt`), the
backups go to `<push target>\.mh-backups`, off the PC (they survive a lost disk); else the PC
folder as today. `KEPT = 3` stays a constant. The other items left in PARTIAL_0352 (guard against
another running container, `--to`/`--from`, the mh script in the archive, e2e) stay there.

## Steps

1. `mh.ps1`/`mh.sh` pick the `/backups` host folder from the push target when there is one.
2. A target not reachable (NAS off): say so, fall back to the PC folder, never fail silently.
3. Tests for both cases; docs en + fr.

## Acceptance

- With a push target, `mh backup` writes into `<target>\.mh-backups`; without, into the PC folder.
