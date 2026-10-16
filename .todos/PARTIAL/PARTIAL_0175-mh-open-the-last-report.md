# 0175 — `mh open`: open the reports in the browser, from the host

- **Priority**: Medium
- **Batch**: launcher
- **Depends**: —
- **Files**: `src/media_hygiene/cli/templates/mh.ps1.j2`, `src/media_hygiene/cli/templates/mh.sh.j2`, `src/media_hygiene/services/launcher.py`, `src/media_hygiene/services/launcher_menu.py`, `src/media_hygiene/services/next_command.py`, `src/media_hygiene/cli/flows.py`, `src/media_hygiene/cli/menu_catalog.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/{en,fr}/clean/quick-guide.md`, `documentation/{en,fr}/clean/04-html-report.md`, `documentation/{en,fr}/commands/launcher.md`, `tests/unit/test_launcher_menu.py`
- **Needs maintainer**: one run on Windows: `mh open` opens the default browser on `index.html` (PowerShell 5.1)

## Why

After `mh audit`, the user must find `index.html` in `$HOME\media-hygiene\reports` by hand
(`cli/flows.py`: "Open index.html in the folder mounted on /reports…"). The container cannot
open a browser; `mh` runs on the host and knows the host folder of `/reports` (it is written in
the script, `script.tools`).

## What to do

- `mh open` is handled by `mh` itself, not by the image: PowerShell
  `Invoke-Item "<reports host folder>\index.html"`; bash `xdg-open` (Linux), `wslview` or
  `explorer.exe` with `wslpath -w` (WSL), `open` (macOS) — which one exists, to check per
  system. No `docker run`.
- `index.html` is the catalogue of every report (`report/index_page.py`, rebuilt by each audit
  and clean): opening it rather than the newest report keeps one command, and the newest is at
  its top. Missing (no audit yet): one line, "No report yet: type mh audit first."
- A reports folder that is a named volume (not a host folder): `mh open` says it cannot open it,
  and how to mount a folder instead.
- Under the launcher (`MEDIA_HYGIENE_LAUNCHER`), the closing line of `audit`/`clean` that says
  where the reports are becomes "👉 `mh open` shows the report in your browser" (`flows.py`).
  Without the launcher, unchanged.
- Listed in the `mh` menu (`menu_catalog.py`), Clean section after `audit`, 🔒.
- Its help: `mh open` is not a command of the image, so `--help` of the image does not list it;
  the `launcher` page and the menu do. Say so in `commands/launcher.md`.

## Acceptance

- Unit: the bash `mh open` with fake `xdg-open`/`wslview` records the path given; no `docker`
  called; missing `index.html` → the line; the PowerShell text holds `Invoke-Item` on the host
  folder of `/reports`, ASCII; `flows.py` line under the launcher.
- Docs both languages: "Clean in short" step 2 ("Read the report": `mh open`), the HTML report
  page, the launcher page; `docs_screenshots` to run (console captures of `audit`).

## Gain (estimated)

Reaching the report: browse to a folder of the home and double-click → one command, the one the
audit itself prints.

## Status — PARTIAL (2026-10-16)

### Done
- `mh open` handled by `mh` itself, without `docker run`, through one host-command mechanism
  shared with 0180/0181 (`services/launcher_host.py`: `HOST_COMMANDS`, dispatched by the first
  word in `mh.ps1.j2` / `mh.sh.j2` before any docker option is built).
- PowerShell: `Invoke-Item -LiteralPath "<reports host folder>\index.html"`; bash: `wslview`,
  `explorer.exe` (with `wslpath -w`), `xdg-open`, `open` (macOS), the same opener as the page
  browser (`_mh_opener`, shared with 0178). Missing `index.html`: "No report yet: type mh audit
  first."; no opener: the file to open by hand; reports in a named volume: said, with the `-v`.
- Under the launcher, the closing tip of `audit`/`clean` is "Type mh open: your browser shows every
  report." (`cli/report_where.py`, moved out of `flows.py` near its cap; a 💡 NEXT tip, not 👉:
  the one 👉 line stays the next step).
- Menu: `open` right after `audit` in the Clean section, 🔒.
- Docs EN/FR: quick guide step 2, HTML report page, launcher page (image `--help` does not list
  it), menu page. Tests: `tests/unit/test_launcher_host.py`.

### Not done
- One run on Windows: `mh open` opens the default browser on `index.html` (PowerShell 5.1).
  **Reason:** needs the maintainer's Windows; step 10a of `tests/measure/mh-measure.ps1`
  (`-Only 10`).
- `docs_screenshots` to run (the menu and audit captures).
  **Reason:** heavy; left to the maintainer.
