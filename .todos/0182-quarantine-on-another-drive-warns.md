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
