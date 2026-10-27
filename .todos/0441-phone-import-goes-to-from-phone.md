# 0441 — `mh import --phone` copies into `From phone\<name>`, as `mh import <folder>`

- **Priority**: Low
- **Batch**: import
- **Depends**: 0379
- **Files**: `src/media_hygiene/cli/templates/mh_phone.ps1.j2`, `src/media_hygiene/services/launcher_phone.py`, `src/media_hygiene/services/launcher_phone_say.py`, `documentation/en/commands/import.md`, `documentation/fr/commands/import.md`
- **Needs maintainer**: one `mh import --phone` with the phone plugged in, after the change

## Decided (review of 2026-10-27)

- The phone's destination becomes `<first photo folder>\From phone\<phone name>` (maintainer),
  consistent with `mh import <folder>` (0378).

## What

- New copies go to `From phone\<name>`; the old `Phone\<name>` is still read as already copied
  (by name and size, as today), so nothing is copied twice; nothing is moved or renamed.
- Docs en+fr; the console lines name the new folder.

## Explicit NON-goals

- Moving the existing `Phone\` folder.
