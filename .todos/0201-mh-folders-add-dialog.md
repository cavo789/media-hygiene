# 0201 — `mh folders add` alone: choose the folder in Windows' folder dialog

- **Priority**: Medium
- **Batch**: launcher
- **Depends**: —
- **Files**: `src/media_hygiene/cli/templates/mh_folders.ps1.j2`, `src/media_hygiene/services/launcher_update.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/unit/test_launcher_folders.py`, `documentation/en/commands/launcher.md`, `documentation/fr/commands/launcher.md`, `documentation/en/start/03-several-folders.md`, `documentation/fr/start/03-several-folders.md`, `tests/measure/mh-measure.ps1`
- **Needs maintainer**: after the work, one run on Windows: step 11 of `mh-measure.ps1`, extended (`mh folders add` alone: the dialog opens in front of the console, cancel changes nothing, the folder chosen is added and read back; Avast says nothing)

## Context

Chosen by the maintainer on 2026-10-17 (proposal A4). 0176 (DONE): `mh folders add <folder>`
writes `mh` again with one more photo folder. Typing a Windows path — quotes, spaces, accents
(0098) — is the hard part for this audience; every competitor with a window offers a folder
picker.

## What to do

- `mh folders add` without a folder opens Windows' folder dialog through COM, as `mh shortcut`
  already uses COM (`WScript.Shell`): `(New-Object -ComObject Shell.Application).BrowseForFolder(…)`.
  No `Add-Type` and no Windows Forms (Avast flagged a compiled `Add-Type`, 2026-10-16). Owner: the
  console's window (`(Get-Process -Id $PID).MainWindowHandle`, 0 when unknown), so that the dialog
  opens in front; root "This PC" (17); options: file-system folders only, new dialog style.
- Cancel: "No folder chosen." and nothing changes. A folder chosen goes through the same checks as
  a typed one: it exists, it has a drive letter (a library, a phone or a network place without a
  letter is refused with the existing message), it is not listed yet. Then the same rewrite and
  read-back as today.
- The dialog's title is translated ("Choose a folder of photos or videos to add"), made shell-safe
  in `UpdateTexts` (`launcher_update.py`).
- Step 11 of `mh-measure.ps1`: `mh folders add` alone, the maintainer chooses the test folder in
  the dialog; then once more, cancelling.

## Explicit non-goals

- `mh folders remove` keeps its argument (it lists the folders already).
- The bash `mh`: no dialog, its usage line unchanged.
- The first `launcher --photos` line of the guide: it runs before `mh` exists.

## Acceptance

- Unit: the rendered `mh.ps1` opens the dialog only for `folders add` without a folder, handles a
  cancel, keeps the checks; ASCII; no `Add-Type`.
- Docs both languages: launcher page, and step 3 ("or `mh folders add` alone: choose it in a
  window").
- Windows (maintainer): step 11 extended.

## Gain (estimated)

Adding a folder: typing a quoted Windows path → two clicks in a familiar window.
