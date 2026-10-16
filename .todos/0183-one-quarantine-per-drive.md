# 0183 — One quarantine per drive: files set aside stay on their own drive

- **Priority**: Medium
- **Batch**: quarantine-drives
- **Depends**: 0182, 0176
- **Files**: `src/media_hygiene/paths/locations.py`, `src/media_hygiene/paths/mounts.py`, `src/media_hygiene/actions/`, `src/media_hygiene/services/clean.py`, `src/media_hygiene/services/undo.py`, `src/media_hygiene/services/status.py`, `src/media_hygiene/cli/cmd_purge.py`, `src/media_hygiene/services/launcher.py`, `src/media_hygiene/cli/templates/mh.ps1.j2`, `src/media_hygiene/cli/templates/mh.sh.j2`, `documentation/{en,fr}/reference-mount-points.md`, `documentation/{en,fr}/clean/08-clean.md`, `documentation/{en,fr}/commands/launcher.md`
- **Needs maintainer**: after the work, a measurement on Windows: time to set aside 1 GB from `E:` to `C:` vs to `E:` (two mounts, so a copy either way)

## Why

The maintainer (2026-10-16) uses the tool on `C:`, `D:` and `E:` and wants three quarantine
folders, one per drive, so that `clean` never fills `C:` with the photos of `E:`. This
changes the mount design (one `/quarantine`, `CLAUDE.md`): the maintainer asked for it.

## Decision (maintainer, 2026-10-16)

Each drive's quarantine is `X:\media-hygiene\quarantine`, mounted on `/quarantine/x`;
`/quarantine` stays the quarantine of `C:` and the default.
Watch: `/quarantine/x` is nested in the `/quarantine` mount, so Docker creates an empty `x`
folder in C:'s quarantine; every reader listing runs of `/quarantine` must skip the
one-letter drive folders (a run id never is one letter: to check).

## What to do

- Mounts: `/quarantine` stays (the default, and for any drive without its own); a quarantine
  per drive is an extra mount the launcher writes for each photo drive (`mh.ps1`, and `mh
  folders add` of 0176 adds it with the folder).
- `clean` sets each file aside in the quarantine of its drive (host source of its data mount),
  else `/quarantine`. The journal already records the target path: `undo` follows it.
- Every reader of the quarantine reads them all: `status`, `history`, `purge`, the `mh`
  menu (`Slot.PURGE`), the age hint, the decisions archive.
- Path-keyed data (`.claude/rules/workflow.md`): a run whose quarantine mount is missing now
  (drive unplugged, `mh` rewritten without it): `undo`/`purge` refuse with the drive to
  plug in, never a partial undo silently.
- Measured first (Needs maintainer): if a copy to the same drive is no faster, the gain is space
  only; say it in the docs.

## Acceptance

- Integration: two data mounts on two fake drives, two quarantines: each file lands in its
  drive's; `undo` restores both; `purge` empties both; a missing quarantine mount → refusal.
- `cache-invalidation-reviewer` agent on the diff (path-keyed journal and quarantine).
- Docs both languages: mount points reference, clean step, launcher page.

## Gain (estimated)

Space used on `C:` by a clean of `E:`: the size of the files set aside → 0.
