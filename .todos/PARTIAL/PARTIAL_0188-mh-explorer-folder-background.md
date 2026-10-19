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

## Status — PARTIAL (2026-10-19)

### Done
- `mh explorer` writes a second key, `HKCU:\Software\Classes\Directory\Background\shell\MediaHygiene`
  (`BACKGROUND_KEY` in `services/launcher_host.py`, derived from `EXPLORER_KEY`), same label, icon
  and command with `%V` (Explorer's open folder on a background click). Both keys written, read
  back and shown one by one (`Saved, read back from <key>:`, the command, the icon; a failure with
  its reason and the antivirus line), then one hint line for both: "Right-click a folder, or the
  empty space of an open folder, then Media Hygiene: the mh menu opens on that folder."
  `mh explorer --remove` removes both, each said (`cli/templates/mh_windows.ps1.j2`).
- French translation of the new hint; the old `{key}` hint is gone (the per-key line reuses the
  existing `Saved, read back from {path}:`).
- Unit: `tests/unit/test_launcher_host.py::test_powershell_explorer_writes_both_keys_and_reads_them_back`
  (both keys, one loop to write and one to remove, the per-key lines, the hint after the loop);
  the error-handling test still counts its four `-ErrorAction Stop` and two catches; ASCII checked
  by the shared rendering helper.
- Docs both languages: launcher page (`mh explorer` row and the keys read back).
- Step 10 of `mh-measure.ps1`: both keys exported before (yours put back after), both commands
  read back, a question for the background click inside `L'ete 2019` and where the entry sits
  (first menu or *Show more options*), both keys checked gone after `--remove`.

### Not done
- The Windows check (maintainer): image built from branch `iterate/2026-10-19`, then
  ```powershell
  cd C:\temp
  Invoke-WebRequest https://raw.githubusercontent.com/cavo789/media-hygiene/iterate/2026-10-19/tests/measure/mh-measure.ps1 -OutFile .\mh-measure.ps1
  Unblock-File .\mh-measure.ps1
  .\mh-measure.ps1 -Only 10 -Count 20
  ```
  (10c: right-click the empty space inside `L'ete 2019` → *Media Hygiene* → the menu opens on that
  folder).
  **Reason:** needs Windows Explorer; not reachable from the devcontainer. Unverified until then:
  that `%V` is the open folder on `Directory\Background` (Microsoft's documented verb variable,
  not checked on the maintainer's Windows), and that `New-Item -Force` creates the missing
  `Directory\Background\shell` parent keys under `HKCU:\Software\Classes`.
- No documentation capture shows `mh explorer`'s output: none is stale.
