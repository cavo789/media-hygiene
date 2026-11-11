# 0700 — The safety card turns green when `mh backup`'s copy on the NAS is proven

- **Priority**: Low
- **Batch**: safety-net
- **Depends**: —
- **Files**: `src/media_hygiene/cli/templates/mh_backup.ps1.j2`, `src/media_hygiene/services/safety.py`, `src/media_hygiene/services/cache_backup.py`
- **Needs maintainer**: a `mh backup` on Windows with a push target set, after the change

Decided by the maintainer on 2026-11-11, review of the iterate of 2026-11-10 (PR #77).

## Context

0689's card keeps "the tool's memory" amber: archives are on `C:`. `mh` already copies them to
`<push target>\.mh-backups` (0419). Decided: no new writer — the Windows side leaves a note of
that copy, read back (archives counted and listed there), and the card turns green on it.

## Acceptance

- [ ] The note written only after the copy is read back; the card reads it
- [ ] Amber again when the note is older than the last backup
