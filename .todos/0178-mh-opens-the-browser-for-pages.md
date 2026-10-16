# 0178 — `mh review` / `review-sort` / `places`: `mh` opens the browser on the page

- **Priority**: High
- **Batch**: launcher
- **Depends**: —
- **Files**: `src/media_hygiene/cli/templates/mh.ps1.j2`, `src/media_hygiene/cli/templates/mh.sh.j2`, `src/media_hygiene/services/launcher.py`, `src/media_hygiene/services/launcher_menu.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/{en,fr}/commands/launcher.md`, `documentation/{en,fr}/clean/10-review-bursts.md`, `tests/unit/test_launcher_menu.py`
- **Needs maintainer**: one run on Windows: `mh review` opens the default browser on the page (PowerShell 5.1)

## Why

The commands serving a page (`script.commands.pages`: `review`, `review-sort`, `places`) print
`http://127.0.0.1:<port>` and the user copies it into a browser. The container cannot open a
browser; `mh` runs on the host and knows the port (`script.commands.port`) and which commands
serve a page. Asked by the maintainer (2026-10-16).

## What to do

- For a page command, `mh` starts a background job on the host that waits until the port answers
  (a check loop with a time limit, e.g. 30 s; never a blind delay), then opens
  `http://127.0.0.1:<port>/`: PowerShell `Start-Process`; bash `xdg-open` / `wslview` /
  `explorer.exe` (WSL) / `open` (macOS), the first that exists (to check per system). The
  `docker run` stays in the foreground (Ctrl+C stops the page as today).
- The page command never opens anything by itself (the container cannot), and without the
  launcher nothing changes.
- `launcher.py` is at 193 lines: put the new script data in `launcher_menu.py` or a new module
  (`.claude/scripts/near_limit.sh` first).
- The line the page command prints under the launcher: "Your browser opens on …; if not, open
  that address" (translated).

## Acceptance

- Unit: rendered PowerShell holds the wait-then-`Start-Process` for page commands only, ASCII;
  bash with a fake `xdg-open` records the URL; a non-page command opens nothing; the port that
  never answers ends the job silently.
- Docs both languages: launcher page, review page (no more "copy the address").

## Gain (estimated)

Reaching the review page: copy an address into a browser → nothing to do.
