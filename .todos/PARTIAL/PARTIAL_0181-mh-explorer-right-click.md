# 0181 — Explorer right-click on a folder: "Media Hygiene" opens the `mh` menu on it

- **Priority**: Medium
- **Batch**: launcher
- **Depends**: 0180
- **Files**: `src/media_hygiene/cli/templates/mh.ps1.j2`, `src/media_hygiene/cli/templates/mh.sh.j2`, `src/media_hygiene/services/launcher.py`, `src/media_hygiene/services/launcher_menu.py`, `src/media_hygiene/cli/menu_catalog.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/{en,fr}/commands/launcher.md`, `documentation/{en,fr}/start/03-several-folders.md`, `tests/unit/test_launcher_menu.py`
- **Needs maintainer**: one run on Windows 10 or 11: right-click a folder → "Media Hygiene" → the menu opens, `audit` chosen analyses that folder (PowerShell 5.1; on Windows 11 the entry may sit under "Show more options": to check)

## Why

The Windows gesture: right-click the folder of photos. Asked by the maintainer (2026-10-16): it
opens the `mh` menu with that folder, not an audit straight away.

## What to do

- `mh --photos "<folder>"` without a command opens the menu, and the step chosen runs with
  `--photos "<folder>"` added (today `--photos` is only parsed when a command follows: the
  menu branch of `mh.ps1` must keep it). The menu says which folder it works on (one line).
- `mh explorer` (handled by `mh.ps1`, like `mh shortcut` of 0180, sharing its host-only
  plumbing): writes `HKCU:\Software\Classes\Directory\shell\MediaHygiene` (label, icon) and its
  `command` = `powershell.exe -NoExit -ExecutionPolicy Bypass -Command ". '<mh.ps1>'; mh
  --photos '%V'"` (quoting of `%V` with spaces and apostrophes: to test). HKCU only: no admin.
  Read back and shown. `mh explorer --remove` deletes the key.
- bash: one line, Windows only.

## Acceptance

- Unit: menu branch with `--photos` passes it to the chosen step (rendered script); registry
  code and `--remove` present, ASCII; a folder name with spaces and `'` quoted right.
- Docs both languages: launcher page; "several folders" mentions the right-click.

## Gain (estimated)

Analysing another folder: type its path → right-click it.

## Status — PARTIAL (2026-10-16)

### Done
- `mh --photos "<folder>"` without a command opens the menu: `--photos` is now parsed before the
  menu branch (both shells), the menu says "The step you choose also analyses: <folder>", and
  the chosen step runs with the `--photos` given.
- `mh explorer` in `mh.ps1` (host-command mechanism of 0175/0180, `_mh_start` shared with
  `mh shortcut`): `HKCU:\Software\Classes\Directory\shell\MediaHygiene` (label, `Icon`) and its
  `command` = `"<powershell.exe>" -NoExit -ExecutionPolicy Bypass -Command ". '<mh.ps1>'; mh
  --from-explorer #" "%V"`. Quoting: Explorer's `%V` sits after `#`, a PowerShell comment, so no
  character of a folder name (apostrophe, `$`, backtick, a trailing `\` of a drive root) can break
  the command; `mh --from-explorer` reads the folder back from `[Environment]::CommandLine`
  (after the last `#" "`, closing quote trimmed). Tested on names with spaces, `'`, `$`, `E:\`.
  Read back (`GetValue('')` compared) and shown; `mh explorer --remove` deletes the key, checked
  gone. HKCU only.
- bash: one line, Windows only. Menu: last section, Windows only.
- Docs EN/FR: launcher page, "several folders" (right-click), menu page, quick guide step 0.

### Not done
- One run on Windows 10 or 11: right-click a folder → "Media Hygiene" → the menu opens on it,
  `audit` chosen analyses that folder; where the entry sits on Windows 11 (first menu or "Show
  more options"); the `#` comment trick works as expected with `powershell.exe -Command`.
  **Reason:** needs the maintainer's Windows; step 10c-10d of `tests/measure/mh-measure.ps1`
  (`-Only 10`; an existing entry is exported and imported back).
- Right-click on the background of an open folder (`Directory\Background\shell`) not added.
  **Reason:** not asked; one more key if wanted.
  → refiled as 0188: add it (maintainer, inbox 2026-10-16).
