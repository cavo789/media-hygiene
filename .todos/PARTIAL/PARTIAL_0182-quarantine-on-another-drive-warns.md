# 0182 — `clean`: say when the quarantine is on another drive than the photos

- **Priority**: High
- **Batch**: launcher
- **Depends**: —
- **Files**: `src/media_hygiene/cli/clean_confirm.py`, `src/media_hygiene/paths/host_paths.py`, `src/media_hygiene/paths/mounts.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/{en,fr}/clean/08-clean.md`, `documentation/{en,fr}/reference-troubleshooting.md`, `tests/unit/test_clean_confirm.py`
- **Needs maintainer**: one run on Windows: photos on `D:` or `E:`, quarantine in `$HOME`: the line appears before the confirmation, with the right drive and size

## Why

The launcher puts the quarantine in `$HOME\media-hygiene\quarantine`, on `C:`. With the photos
on `E:`, each file set aside is copied to `C:` and fills it (Windows' system drive, often the
smallest). Asked by the maintainer (2026-10-16).

## What to do

- Before the confirmation of `clean`, from the mount table (host sources of the data mounts and
  of `/quarantine`, `host_paths`): the drives of the files to set aside that differ from the
  quarantine's. One warning line per run: "N files (X GB) will be copied from E: to the
  quarantine on C: (Y GB free there)" (free space by `shutil.disk_usage` on `/quarantine`).
- Not enough free space: refuse before anything moves, saying how much is missing.
- Unknown host source (Linux, named volume): no line.
- Note (checked in `actions/no_overwrite.py`): two `-v` mounts are two filesystems inside the
  container, so even on the same drive a quarantine move is a copy (EXDEV), not a rename. The
  line is about space, not speed.

## Acceptance

- Unit: the line with photos on `E:` and quarantine on `C:`; none on the same drive; refusal
  when free space is short; no line without host sources.
- Docs both languages: clean step page and troubleshooting ("C: is full after clean").
- Console output changes: `docs_screenshots` to run.

## Gain (estimated)

A `clean` that silently fills `C:` → told before, refused when it cannot fit.

## Status — PARTIAL (2026-10-16)

### Done
- `paths/drives.py`: `Drives.drive_of` (the drive of a container path, from the Windows sources
  of the mount table only) and `QuarantineRoute` (`receiving`: the quarantine of a file, per
  drive through `by_drive`, else `/quarantine`; `crosses_drive`) — written for 0183 to fill
  `by_drive`.
- `services/quarantine_space.py`: the files `clean` moves (`set_aside`: copies unless
  `--delete`, near, bursts, unreadable, orphans), grouped by receiving quarantine when they
  come from another drive, with `shutil.disk_usage` free space; `QUARANTINE_HEADROOM` = 1 GiB
  kept free.
- `cli/clean_space.py`, called by `confirm_clean` before the question (with `--yes` too): one
  warning line "N files (X GB) will be copied from E: to the quarantine on C: (Y GB free
  there)."; a `MountError` with what is missing when it does not fit — before any move or
  journal entry. No line on the same drive, without host sources, or when the free space
  cannot be read.
- Tests: `tests/unit/test_clean_space.py` (line, same drive, no source, refusal, `--delete`
  counts, unreadable free space, route), `tests/integration/test_quarantine_space.py`
  (refusal: data, journal and quarantine untouched; with room: the line, then the clean).
- Docs EN/FR: `clean/08-clean.md` (section "Photos on another drive than the quarantine",
  refusals bullet), `reference-troubleshooting.md` ("C: is full after a clean"). French
  catalog translated.
- `tests/measure/mh-measure.ps1` step 12.

### Not done
- The check on Windows: photos on `D:`/`E:`, quarantine in `$HOME`: the line appears before
  the confirmation with the right drives, size and C:'s free space (against Windows' figure);
  none with the quarantine on the photos' drive.
  **Reason:** needs the maintainer's Windows + Docker Desktop (that `shutil.disk_usage` on a
  Docker Desktop bind mount reports the host drive's free space is unchecked). Run
  `powershell -ExecutionPolicy Bypass -File .\mh-measure.ps1 -Only 12 -Count 20 -OtherDrive E:`.
- `docs_screenshots` not run (console output changed only in the cross-drive case, which the
  synthetic captures do not show: captures likely unchanged).

## Inbox (2026-10-19)

- `docs_screenshots`: stale — the synthetic captures never show the cross-drive line.
- The Windows check: still waiting (`mh-measure.ps1`, step 13).
