# 0186 — `undo`/`purge`: find a run whose drive came back under another letter

- **Priority**: Medium
- **Batch**: quarantine-drives
- **Depends**: —
- **Files**: `src/media_hygiene/paths/drives.py`, `src/media_hygiene/services/undo.py`, `src/media_hygiene/services/undo_guard.py`, `src/media_hygiene/cli/cmd_purge.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/{en,fr}/clean/08-clean.md`, `documentation/{en,fr}/reference-troubleshooting.md`, `tests/integration/test_quarantine_drives.py`

## Why

Follows 0183 (PARTIAL). A USB drive set aside as `E:` and plugged back as `F:`: the journal
says `/quarantine/e/<run>/…`, `undo` refuses "plug in E:", while the files sit in
`F:\media-hygiene\quarantine\<run>`. Decided by the maintainer (inbox, 2026-10-16): look for
the run in the other quarantines.

## What to do

- When the journal's quarantine for a run is not mounted, look for the run's folder (its id is
  unique) in every mounted quarantine (`/quarantine` and each `/quarantine/x`); found in exactly
  one: use it, and say it in one line ("run … found in F:'s quarantine, not E:'s").
- The originals' paths: the photos of that drive moved too (`/data/e/…` → `/data/f/…`). Restore
  only when the original's folder exists under the new letter (same relative path); else refuse
  per file, naming it. Never restore onto another drive's path by guess.
- Found in two quarantines: refuse, naming both (a copy made by hand).
- `purge <run>`: the same search.

## Acceptance

- Integration: run set aside on fake drive `e`, mounts rebuilt as `f`: `undo` finds and restores
  it, says so; found in two: refusal; original folder missing: per-file refusal.
- `cache-invalidation-reviewer` on the diff (path-keyed journal).
- Docs both languages: clean step, troubleshooting "another letter".

## Gain (estimated)

An undo after a USB drive changed letter: impossible without Disk Management → works.
