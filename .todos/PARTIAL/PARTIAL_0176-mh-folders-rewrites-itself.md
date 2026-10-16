# 0176 — `mh folders`: list, add, remove a folder; `mh` rewrites itself

- **Priority**: Medium
- **Batch**: launcher
- **Depends**: —
- **Files**: `src/media_hygiene/cli/templates/mh.ps1.j2`, `src/media_hygiene/cli/templates/mh.sh.j2`, `src/media_hygiene/services/launcher.py`, `src/media_hygiene/services/launcher_folders.py`, `src/media_hygiene/services/launcher_menu.py`, `src/media_hygiene/cli/cmd_launcher.py`, `src/media_hygiene/cli/menu_catalog.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/{en,fr}/start/03-several-folders.md`, `documentation/{en,fr}/commands/launcher.md`, `documentation/{en,fr}/clean/quick-guide.md`, `tests/unit/test_launcher_folders.py`, `tests/e2e/test_launcher_image.py`
- **Needs maintainer**: one run on Windows: `mh folders add "D:\X"`, then a new terminal, `mh audit` sees it (PowerShell 5.1)

## Why

Adding a folder today means typing the long `docker run … launcher --photos … --photos …`
again, every folder included (0173), and the guides say so. `mh` already holds its folders: it
can rewrite its own file.

## What to do

- `mh.ps1`/`mh.sh` keep the arguments of the `launcher` run that wrote them: the folders
  (`--photos`, `--quarantine`), `--locale`, the `-v` of tool folders, as one list in the script
  (one variable, e.g. `$mhLauncher = @('--photos', 'C:\Photos', …)`, ASCII like the rest).
- `mh folders`: lists the photo folders and the quarantine, each said present or not plugged in.
- `mh folders add "D:\X"` / `mh folders remove "D:\X"`: run `launcher` again through the image
  with the kept arguments ± that folder, write to a temporary file next to the script, move it
  over `mh.ps1` only when `launcher` succeeded (a refused folder — nested, network — leaves the
  old `mh` intact, unlike `> mh.ps1`), load it again (`. $script` / `source`), then show the
  list read back from the new file (a save is proven by reading it back).
- `remove` of the last photo folder: refused, with the line saying `mh` needs at least one.
- Which file to rewrite: the script knows its own path (`$PSCommandPath` is empty inside a
  function: the path is written into the script by `launcher`, `script_path(shell)`, or
  `$MyInvocation` when loaded — to check in PowerShell 5.1).
- In the menu (`menu_catalog.py`): not a step of the guides; one line under the menu, "Your
  folders: mh folders".

## Acceptance

- Unit: the kept arguments rendered in both shells, ASCII, accents rebuilt; bash `mh folders
  add` with a fake `docker` writing a new script → file replaced, reloaded, listed; a failing
  `launcher` → old file intact, message; `remove` of the last folder refused.
- e2e: `mh folders add` on the demo volumes, then `mh audit`.
- Docs both languages: "Several folders" (`mh folders add` replaces "run launcher again"), the
  launcher page.

## Gain (estimated)

One more folder: the long line with every folder retyped → `mh folders add "D:\X"`.

## Status — PARTIAL (2026-10-16)

### Done
- `services/launcher_kept.py`: the `launcher` run kept in the script, each word quoted for its
  shell (`$`, backtick, quotes escaped; `mh.ps1` still ASCII): `-e` settings, `-v` of a tool
  folder mounted by hand or of a photo folder mounted elsewhere than `/data/<drive>/…` (kept,
  never removed by `mh`), the global `--locale`, `launcher --shell … --quarantine …`, then the
  photo folders apart (`_mh_photos`), given back as `--photos`. The quarantine stays its own
  option, so 0183 (one quarantine per drive) can add its own words.
- `mh folders` (list, each folder and the quarantine *found* / *not found*), `mh folders add`
  (folder must exist; case-insensitive duplicate check on Windows), `mh folders remove` (works
  on a folder gone: renamed, moved, disk unplugged; the last one refused). Templates
  `cli/templates/mh_folders.{ps1,sh}.j2`, included by `mh.{ps1,sh}.j2`; dispatched like the other
  host commands (`launcher_host.HOST_COMMANDS`).
- Rewrite: `launcher` run again through the image into `<file>.new`, moved over the script only
  when it succeeded and wrote something, then loaded again and its folders listed from the new
  file ("Saved, read back from …"). The file is `$MyInvocation.MyCommand.ScriptBlock.File`
  (PowerShell) / `${BASH_SOURCE[0]}` resolved at load time (bash). PowerShell functions are now
  declared `function global:…` so that reloading from inside `mh` reaches the global scope.
- Fixed on the way: the PowerShell dispatch passed `@($rest | Select-Object -Skip 1)` as ONE
  array argument, so `mh explorer --remove` never saw `--remove`; now splatted (`@more`).
- `launcher` under `mh` (`MEDIA_HYGIENE_LAUNCHER` set) no longer says "Load it with…".
- Menu: one line under it, "Your folders: mh folders. A new version: mh update." (`menu_view.py`).
- Tests: `tests/unit/test_launcher_rewrite.py` (bash with a fake `docker` running the real
  `launcher`: add/reload/read back, renamed folder removed, failing launcher leaves the file,
  refusals; kept run; PowerShell text: ASCII, order run → check → Set-Content → Move-Item →
  reload; global functions, splat); e2e `mh folders add`/`remove` then `mh audit`.
- Docs en/fr: launcher page (new sections), "Several folders", "Clean in short".
- `tests/measure/mh-measure.ps1` step 11 (11a-11d).

### Not done
- The Windows run: `mh folders add "D:\X"`, then a new terminal, `mh audit` sees it
  (PowerShell 5.1): `Move-Item -Force` over the loaded `mh.ps1`, `global:` reload, `6>&1`.
  **Reason:** no PowerShell in the devcontainer; step 11 of `tests/measure/mh-measure.ps1`
  (`powershell -ExecutionPolicy Bypass -File .\mh-measure.ps1 -Only 11 -Count 20`).
- e2e adds a host folder but audits only after removing it: Docker cannot create a bind's
  mount point inside the read-only demo volume of `/data`.
  **Reason:** e2e data is a named volume; the add-then-audit path is in step 11b instead.
