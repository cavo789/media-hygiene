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
Only the quarantine moves per drive (maintainer, 2026-10-16): config, journal, reports and the
cache stay single, in `$HOME\media-hygiene` (one index finds duplicates across drives, one
journal records each file's quarantine path, so `undo` follows it).
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

## Status — PARTIAL (2026-10-16)

### Done
- `paths/quarantines.py` (`Quarantines`): the per-drive quarantines are the mounts
  `/quarantine/<one lowercase letter>`; `QuarantineRoute.by_drive` is filled from them
  (`services/quarantine_space.py`), `CleanContext.route` + `run_folder()` send each file of
  `clean` (and sort's junk) to `<its drive's quarantine>/<run>/…`, else `/quarantine/<run>`.
  The journal records that path; `undo` follows it (unchanged).
- Readers read every quarantine: `actions/purge.py` (`runs_in`, `run_folders`), `status`
  (hence the menu's `Slot.PURGE` and the age hint), `purge` (a run on two drives erased on
  both), the clean confirmation line (every quarantine named). History reads journals only;
  the decisions archive does not read the quarantine: nothing to change there.
- `services/quarantines.py`: `undo` and `purge <run>` refuse a run whose `done` quarantine
  moves point into `/quarantine/<x>` not mounted now, naming the drive; `purge` alone keeps
  such runs and names them (cache-invalidation-reviewer finding). The one-letter folder Docker
  leaves in `/quarantine` is never a run (run ids start with 8 digits; `purge e` refused).
- Persistence: a per-drive quarantine is only ever a mount, hence persistent; `/quarantine`
  stays required by `clean` as before. Writability and the "tool folder inside photos" check
  cover the per-drive ones.
- Launcher (`services/launcher_drives.py`): one `-v "X:\media-hygiene\quarantine:/quarantine/x"`
  per photo drive other than the quarantine's own (`C:` by default; WSL `/mnt/x/…` too), created
  by `mh` before each run, listed by `mh folders`; none for a drive whose photo folder holds it
  (`E:\`). `mh folders add` rewrites `mh`, so a new drive gets its own. The `docker run` printed
  after a command (without `mh`) carries the per-drive mounts of the run.
- 0182's line now appears only for a drive without its own quarantine; its refusal tip points
  to `/quarantine/<x>`.
- Tests: `tests/integration/test_quarantine_drives.py`, `tests/unit/test_quarantine_drives.py`,
  `tests/unit/test_clean_space.py`. Docs EN/FR (mount points, clean step 8, launcher,
  troubleshooting), CLAUDE.md, French catalog. `tests/measure/mh-measure.ps1` step 13.

### Not done
- The measurement on Windows: time to set aside 1 GB from `E:` to `C:` against `E:` to `E:`
  (two mounts: a copy either way), and the docs sentence about speed that depends on it.
  **Reason:** needs the maintainer's Windows + Docker Desktop and a second drive:
  `powershell -ExecutionPolicy Bypass -File .\mh-measure.ps1 -Only 13 -Count 20 -OtherDrive E:`
  (13a/13b against 13c/13e; 13d must refuse naming the drive).
- A USB drive that comes back under another letter: the journal says `/quarantine/e/…`, the
  refusal asks for `E:`. Same limit as every path in the journal; not handled.
  → refiled as 0186: look for the run in the other quarantines (maintainer, inbox 2026-10-16).

## Inbox (2026-10-20)

- The Windows measurement (steps 12 and 13 of mh-measure.ps1) needs a second **fixed** disk: the
  maintainer has none (a USB stick is refused by those steps since 2026-10-20: Docker Desktop
  cannot see it without mh's sharing). Not a maintainer item any more: the behaviour stays
  covered by the unit and integration tests; a contributor with a second disk may run
  `.\mh-measure.ps1 -Only "12,13" -Count 20 -OtherDrive <letter>:`.
- Every other item done or refiled → closed DONE.
