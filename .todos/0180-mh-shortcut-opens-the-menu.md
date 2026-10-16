# 0180 — `mh shortcut`: a "Media Hygiene" icon on the Desktop and in the Start menu

- **Priority**: Medium
- **Batch**: launcher
- **Depends**: —
- **Files**: `src/media_hygiene/cli/templates/mh.ps1.j2`, `src/media_hygiene/services/launcher.py`, `src/media_hygiene/services/launcher_menu.py`, `src/media_hygiene/cli/menu_catalog.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/{en,fr}/start/00-install-docker.md`, `documentation/{en,fr}/commands/launcher.md`, `tests/unit/test_launcher_menu.py`
- **Needs maintainer**: one run on Windows: `mh shortcut`, then double-click the icon: a PowerShell window opens on the `mh` menu and stays open (PowerShell 5.1)

## Why

A user who never opens PowerShell should still reach the menu: double-click an icon. Asked by
the maintainer (2026-10-16): the icon opens a PowerShell window showing the `mh` menu.

## What to do

- `mh shortcut` is handled by `mh.ps1` itself (no `docker run`, like `mh open` of 0175): through
  `WScript.Shell` `CreateShortcut`, write `Media Hygiene.lnk` on the Desktop and in the Start
  menu (`[Environment]::GetFolderPath('Desktop')`, `'Programs'`), target `powershell.exe
  -NoExit -ExecutionPolicy Bypass -Command ". '<mh.ps1>'; mh"`. It loads the script itself, so
  it works even without the profile line; `-ExecutionPolicy Bypass` for this process only (to
  check it is enough with the user's policy).
- Proven: read the `.lnk` back (`CreateShortcut` on the same path, `TargetPath` and
  `Arguments`) and print where both are (product rule: a save is shown from disk).
- Run again: rewritten, same names. A OneDrive-redirected Desktop works through `GetFolderPath`.
- bash: `mh shortcut` says it is for Windows (one line).
- In the `mh` menu, last section (setup), 🔒.

## Acceptance

- Unit: rendered PowerShell holds the shortcut code, the target, `-NoExit`, ASCII; bash prints
  the one line.
- Docs both languages: step 0 offers it after the profile line; launcher page.

## Gain (estimated)

Starting the tool: open PowerShell and type `mh` → double-click an icon.
