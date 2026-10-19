# 0219 — `mh phone`: copy only the new photos and videos of a phone plugged in over USB

- **Priority**: Medium — a large feature the maintainer asked for: "if it is possible, it is a big new feature"
- **Batch**: launcher
- **Depends**: 0218, 0216
- **Files**: `src/media_hygiene/cli/templates/mh_phone.ps1.j2` (new), `src/media_hygiene/cli/templates/mh.ps1.j2`, `src/media_hygiene/services/launcher_host.py`, `src/media_hygiene/services/launcher_phone.py` (new), `src/media_hygiene/cli/cmd_phone_plan.py` (new), `src/media_hygiene/services/phone_plan.py` (new), `src/media_hygiene/cli/app.py`, `src/media_hygiene/cli/safety.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/unit/test_phone_plan.py` (new), `tests/unit/test_launcher_phone.py` (new), `documentation/en/commands/launcher.md`, `documentation/fr/commands/launcher.md`, `documentation/en/start/03-several-folders.md`, `documentation/fr/start/03-several-folders.md`, `tests/measure/mh-measure.ps1`

## Context

Chosen by the maintainer on 2026-10-17 (proposal F9): "we plug our smartphone in and copy 100 % of
the photos and videos each time; it would be great to copy only the new ones". Comparing folders
(`--photos C:\Photos --photos E:\Photos`) already finds the duplicates after a copy; this avoids
the copy itself, and with it the cleaning that follows.

A phone over USB has no drive letter: Docker cannot see it, PowerShell can (0218). Only the
container knows what the library already holds (the index, in the cache volume) and what the user
set aside before (the journals, 0216). So the work is split: `mh` (PowerShell, on Windows) reads
and copies, the container decides.

## Measured (step 19 of `mh-measure.ps1`, 2026-10-19, maintainer's Samsung A72, Android, PowerShell 5.1)

- The phone: one item of This PC (`Namespace(17)`) with `IsFileSystem` False, `Type` "Mobile Phone",
  named by its owner ("A72 de …"). One top folder, **localised** ("Stockage interne"): find `DCIM`
  by walking (as step 19 does), never by a fixed path.
- `DCIM` listed through `Items()`: 775 files in 24.0 s (≈ 31 ms per file, measured): for 5,000
  files, ≈ 2.5 min just to list (estimated): say it with a progress line.
- Extensions seen: `.jpg` 663, `.png` 85, `.mp4` 14, `.jpeg` 12, `.webp` 1; names such as
  `20250512_195342.jpg`, `Screenshot_…`, `Messenger_creation_<GUID>.jpeg`, `1763843759164.jpg`
  (epoch milliseconds), `received_….png`.
- **Over MTP, `.Size` is 0 and `.ModifyDate` is 1899-12-30 (no value)** for every file: the size is
  `ExtendedProperty('System.Size')`, the date `ExtendedProperty('System.DateModified')`, in **UTC**
  (`20250512_195342.jpg` → 17:53:43, Brussels summer time); `System.DateCreated` is empty.
- A copy (`CopyHere`, flags 4+16+1024) keeps the phone's modified time (shown in local time), its
  creation time is the copy's.
- Copying again a file the destination already holds opens Windows' "replace" dialog **despite
  flag 16** (not honoured for MTP), and it opens **behind the console**: the maintainer found
  about ten of them only with Alt+Tab; the second round of 20 files took 386.3 s instead of 2.0 s
  (measured), all spent waiting for a person. "Copy and overwrite" left the 20 copies identical
  (size and modified time unchanged). Hence below: copy only into a folder that cannot hold the
  name yet — a dialog must never be possible.
- Not measured (script bug, fixed since): the speed, and whether "size reached" proves a finished
  copy — the size was read as 0, so each wait returned at once. To measure by the end-to-end run.
- The maintainer does not leave the phone plugged in: an import is a session of a few minutes, and
  an unplugged cable in the middle must be handled.

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
- **Never** deletes, moves or renames anything on the phone: freeing the phone is 0248, which
  reuses this plan — so `phone-plan` prints each file's case with its reason: new (to copy),
  in the library (which file), set aside on purpose (which run, still in the quarantine or
  purged), already at the destination.
- From the measurement: size and date from the extended properties (`System.Size`,
  `System.DateModified` UTC), never `.Size`/`.ModifyDate`; each file copied into an **empty staging
  folder** of the run (`<destination>\.mh-phone-<run>`), waited for until its length equals
  `System.Size` (and stops growing), then moved with `Move-Item` to its place — a name already there
  is never overwritten (`_1` added, said), so Windows never asks anything. A file that never
  arrives (cable pulled, 60 s): the partial copy removed, the import stopped with what was copied
  so far said ("unplugged? type `mh phone` again: what is already copied is skipped"); the staging
  folder removed at the end.
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
- Windows (maintainer, after the work; closes the TODO, implementing needs no maintainer — inbox 2026-10-19): step 19 with the end-to-end run (`mh phone` twice, the second copies nothing; the speed in MB/s; the cable pulled once in the middle).

## Gain (estimated)

Each import of a phone: copying every photo and video again (gigabytes, then a clean of the
duplicates) → copying only the new ones; for a phone holding 5,000 files of which 200 are new,
≈ 96 % less to copy (estimated from those numbers, the speed to be measured by step 19).

## Status — PARTIAL (2026-10-19)

### Done
- `mh phone [--to <folder>]` in `mh.ps1` (`cli/templates/mh_phone.ps1.j2`, values and translated
  messages in `services/launcher_phone.py`; dispatched as a host command, `PHONE` in
  `launcher_host.py`; the bash `mh` says "mh phone is for Windows only."). Shell.Application only,
  no Add-Type; `CopyHere` only, never `MoveHere`. The phone: items of This PC (17) that are
  folders without a file system; one taken, several numbered and asked. `DCIM` found by walking
  (three levels). Listing with `System.Size`, `System.DateModified` (UTC, ISO, invariant culture),
  the name from `System.FileName` (else `.Name`: extensions hidden by Explorer would drop it), a
  line every 500 files; the phone looked for again after the listing (a cable pulled there stops
  before anything is decided).
- Destination: `--to`, else `<first photo folder>\Phone`, then `<phone name>` (characters Windows
  refuses replaced by `_`), the phone's folders below `DCIM` kept.
- `media-hygiene phone-plan` (`cli/cmd_phone_plan.py`, `services/phone_plan.py`,
  `services/phone_known.py`): hidden from `--help`, read-only (in `READ_ONLY_COMMANDS`, a data
  command: messages on stderr), reads `path<TAB>size<TAB>date` lines on stdin (UTF-8), prints one
  line per file: `case<TAB>path<TAB>size<TAB>date<TAB>reason…` with the cases `new`, `library`
  (+ host path of the file), `set-aside` (+ run, `quarantine`/`purged`, date, kind — what 0248
  needs for its two warnings), `destination` (+ relative path). Order: library, then journals,
  then destination. Name compared case-folded, size equal; ties: first index path in order, the
  latest set-aside. The journals through `remembered_of` (0216: honours `[clean] returned`), the
  quarantine state from `runs_in(mounted_quarantines)`. Empty index: a warning to run
  `mh audit` first.
- `mh` runs it with `-i` (no `-t`), photos and backups `:ro`, the tool folders and drive
  quarantines, the destination mounted `:ro` at its `/data/<x>/...` point; UTF-8 both ways.
- Copy: each file into an empty staging folder `<destination>\.mh-phone-<date>` (leftovers of a
  stopped run removed first, skipped by `phone-plan`), waited for until its length equals
  `System.Size` (size unknown: until it stops growing) **and** it opens exclusively (the copy
  engine let it go); 60 s without growth: the partial copy removed, the import stopped with the
  count copied so far and "type mh phone again". Then `Move-Item` without `-Force` to a free name
  (`_1`, `_2`…, said); the staging folder removed in a `finally`.
- Summary read back from the destination (each copy found with the phone's size): copied count,
  GB, MB/s; then library / set aside / already copied counts; one 👉 `mh audit` line last.
- Tests: `tests/unit/test_phone_plan.py` (16: each reason, case ignored, ties, undo forgets,
  latest set-aside, staging ignored, empty cache warning, unreadable lines, UTF-8, hidden from
  help), `tests/unit/test_launcher_phone.py` (15: functions, CopyHere only, no MoveHere/Add-Type,
  extended properties, staging then move, wait, never overwritten, mounts, French, safe texts,
  bash Windows only); `test_help_panels.py` ignores hidden commands; `phone-plan` added to the
  read-only runs of `tests/integration/test_read_only_commands.py`.
- Docs both languages: launcher page (`mh phone` row and section: what is skipped, name+size is
  no proof, cable pulled, staging folder, Windows only), step 3 ("A phone? Copy only its new
  photos"). French catalogue translated.
- Step 19 of `mh-measure.ps1`: 19c logs `System.FileName`; 19h–19k (asked first, it copies the
  whole `DCIM` under `-Work`): `mh phone` twice (wall time, files copied, read back, staging
  folders left), the 5 largest copies removed and copied again while the cable is pulled out
  (lines, wall time, any window), plugged in again, the rest copied; `_1` names counted.

### Not done
- The Windows end-to-end check (maintainer): image built from branch `iterate/2026-10-19`, then
  ```powershell
  cd C:\temp
  Invoke-WebRequest https://raw.githubusercontent.com/cavo789/media-hygiene/iterate/2026-10-19/tests/measure/mh-measure.ps1 -OutFile .\mh-measure.ps1
  Unblock-File .\mh-measure.ps1
  .\mh-measure.ps1 -Only 19 -Count 1
  ```
  (answer `y` at 19h; the second `mh phone` must copy nothing; the speed in MB/s; the cable pulled
  at 19j: no window, the partial copy and the staging folder gone, 19k copies the rest).
  **Reason:** needs Windows, Docker Desktop and the phone; not reachable from the devcontainer.
  Unverified until then: that "length = System.Size and opens exclusively" proves a finished MTP
  copy, `System.FileName` over MTP, and Windows PowerShell 5.1 piping the listing to `docker run -i`.
- No documentation capture is stale (`phone-plan` is hidden; no captured output changed).
