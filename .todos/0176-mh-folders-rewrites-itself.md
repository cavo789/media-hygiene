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
