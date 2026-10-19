# 0188 — `mh explorer`: also the right-click on the background of an open folder

- **Priority**: Low
- **Batch**: launcher
- **Depends**: —
- **Files**: `src/media_hygiene/cli/templates/mh.ps1.j2`, `src/media_hygiene/services/launcher_host.py`, `documentation/{en,fr}/commands/launcher.md`, `tests/unit/test_launcher_host.py`, `tests/measure/mh-measure.ps1`

## Why

Follows 0181 (PARTIAL), which adds the entry on a folder's icon only. Decided by the maintainer
(inbox, 2026-10-16): add it on the background of an open folder too.

## What to do

- `mh explorer` writes a second key, `HKCU:\Software\Classes\Directory\Background\shell\MediaHygiene`,
  same label, icon and command, with `%V` (the open folder: to check it is `%V` here too). Read
  back and shown like the first. `mh explorer --remove` removes both.
- Step 10 of `mh-measure.ps1` reads the second key back and asks for the background click.

## Acceptance

- Unit: the rendered `mh.ps1` writes, reads back and removes both keys, ASCII.
- Docs both languages: launcher page.
- Windows (maintainer, after the work; closes the TODO, implementing needs no maintainer — inbox 2026-10-19): one run on Windows: right-click the empty space of an open folder → "Media Hygiene" → the menu opens on that folder (step 10 of `mh-measure.ps1`, extended)

## Gain (estimated)

Inside the folder already: go up one level to right-click it → right-click where you are.
