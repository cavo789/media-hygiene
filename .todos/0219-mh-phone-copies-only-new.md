# 0219 — `mh phone`: copy only the new photos and videos of a phone plugged in over USB

- **Priority**: Medium — a large feature the maintainer asked for: "if it is possible, it is a big new feature"
- **Batch**: launcher
- **Depends**: 0218, 0216
- **Files**: `src/media_hygiene/cli/templates/mh_phone.ps1.j2` (new), `src/media_hygiene/cli/templates/mh.ps1.j2`, `src/media_hygiene/services/launcher_host.py`, `src/media_hygiene/services/launcher_phone.py` (new), `src/media_hygiene/cli/cmd_phone_plan.py` (new), `src/media_hygiene/services/phone_plan.py` (new), `src/media_hygiene/cli/app.py`, `src/media_hygiene/cli/safety.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/unit/test_phone_plan.py` (new), `tests/unit/test_launcher_phone.py` (new), `documentation/en/commands/launcher.md`, `documentation/fr/commands/launcher.md`, `documentation/en/start/03-several-folders.md`, `documentation/fr/start/03-several-folders.md`, `tests/measure/mh-measure.ps1`
- **Needs maintainer**: the results of step 19 of `mh-measure.ps1` (0218) with one or two phones (an Android one, and an iPhone if one is at hand): the device and `DCIM` names, the properties giving a file's size and date, how to know a copy has finished, the speed

## Context

Chosen by the maintainer on 2026-10-17 (proposal F9): "we plug our smartphone in and copy 100 % of
the photos and videos each time; it would be great to copy only the new ones". Comparing folders
(`--photos C:\Photos --photos E:\Photos`) already finds the duplicates after a copy; this avoids
the copy itself, and with it the cleaning that follows.

A phone over USB has no drive letter: Docker cannot see it, PowerShell can (0218). Only the
container knows what the library already holds (the index, in the cache volume) and what the user
set aside before (the journals, 0216). So the work is split: `mh` (PowerShell, on Windows) reads
and copies, the container decides.

## What to do

- **`mh phone [--to <folder>]`**, a host command of `mh` (as `shortcut`, `folders`), PowerShell
  only, in a new template `mh_phone.ps1.j2`:
  1. find the phone as step 19 found it (one phone: taken; several: a numbered choice), then its
     `DCIM`;
  2. list its files: name, size, date (the properties step 19 found);
  3. pipe that list (one line per file: relative path, name, size, date) to a hidden data command
     of the image, run with the photos `:ro`, the cache and the journal:
     `media-hygiene phone-plan` reads stdin, prints the files to copy;
  4. copy those, and only those, with `CopyHere` (no dialog), each one waited for as step 19 found,
     into the destination folder: `--to`, else `<first photo folder>\Phone`, then a subfolder per
     phone name; the phone's folders below `DCIM` kept;
  5. say what happened, read back from the destination: "212 new photos and videos copied
     (1.4 GB); 4,980 already in your library; 31 set aside before, not copied" and the next step
     (`👉 mh audit`).
- **`phone-plan`** (container, hidden from `--help`: plumbing for `mh` only; check that the docs
  tests accept a hidden command, or give it a short page): a file is not copied when the library
  already holds a file of the same name (case ignored) and the same size (the index), when the
  journals remember it as set aside by the user (0216, by name and size: the phone gives no
  content to hash), or when the destination already holds it.
- **Never** deletes, moves or renames anything on the phone.
- Name and size are not a proof of identity (the phone gives no content); a file wrongly taken for
  "already there" stays on the phone, and a file copied twice is found by the next audit as an
  identical copy: say both in the docs.
- Step 19 of `mh-measure.ps1` gains the end-to-end run: `mh phone` twice in a row, the second copies
  nothing.

## Explicit non-goals

- The bash `mh` (no phone access from WSL or Linux).
- Moving the new files into the sorted tree: `classify` and `sort` do it, as for any folder.
- Folders other than `DCIM` (WhatsApp, Screenshots): later, if wanted.

## Acceptance

- Unit (`test_phone_plan.py`): a list on stdin against an index, journals and a destination: each
  reason to skip, names compared without case, the output format; (`test_launcher_phone.py`): the
  rendered `mh.ps1` holds `phone`, `CopyHere` only (never `MoveHere`), the wait per file, ASCII.
- Docs both languages: the launcher page, step 3 ("copy only the new photos of your phone").
- Windows (maintainer): step 19 with the end-to-end run.

## Gain (estimated)

Each import of a phone: copying every photo and video again (gigabytes, then a clean of the
duplicates) → copying only the new ones; for a phone holding 5,000 files of which 200 are new,
≈ 96 % less to copy (estimated from those numbers, the speed to be measured by step 19).
