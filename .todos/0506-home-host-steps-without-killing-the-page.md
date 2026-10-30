# 0506 — Host steps and "Ctrl+C then type" without killing the page

- **Priority**: High
- **Batch**: launcher
- **Depends**: 0505
- **Files**: `src/media_hygiene/services/launcher_host.py`, `src/media_hygiene/cli/templates/mh.ps1.j2`, `src/media_hygiene/review/templates/home_run.js.j2`, `src/media_hygiene/review/templates/album_bar.html.j2`, `src/media_hygiene/review/home_texts.py`, `tests/unit/`, `tests/measure/mh-measure.ps1`, `documentation/en/commands/launcher.md`, `documentation/fr/commands/launcher.md`
- **Needs maintainer**: a run on Windows PowerShell 5.1 + Docker Desktop (with Avast) of the new host path

## Reported (maintainer, 2026-10-30)

Sharing an album, the album bar said "close this page (Ctrl+C in the window where mh runs),
then type (copied): …" (`album_bar.html.j2`, `tv` and `send`). The maintainer preferred to
open a **second** PowerShell window and type the command there, keeping the page alive.
That is what the page should do itself.

## Today

- `HOST_COMMANDS` (`launcher_host.py`: `open`, `shortcut`, `explorer`, `folders`, `update`,
  `push`): the server ends, `mh.ps1` runs the step on Windows, then opens the page again.
- The album bar's `tv` / `send` commands: the user is told to Ctrl+C and type them.

## To do

1. Container steps (`send`, `tv` when they need no new mount or port): run them through
   0505's in-page runner instead of "Ctrl+C then type". Check, per command, why a restart
   was needed (another mount? another port for the slideshow?) and keep the restart only
   where it truly is.
2. Host steps: `mh.ps1` keeps the page's container running and runs the step beside it
   (a background job or a second process, **no run-time compile**: Avast, see
   `Add-Type`), its output written to a file under the mh home; the page polls a route
   and shows it in 0505's dialog. `update` keeps its restart (new image).
3. Fallback when the host cannot run beside the page: say "open a second PowerShell
   window and type (copied): …" — never Ctrl+C first.
4. PowerShell 5.1 only, ASCII; a step in `tests/measure/mh-measure.ps1` proves it on the
   maintainer's PC.
5. Docs EN + FR; `docs_screenshots` should run after.
