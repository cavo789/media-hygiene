# 0174 — `mh`: "Docker Desktop is not started" instead of Docker's own error

- **Priority**: High
- **Batch**: launcher
- **Depends**: —
- **Files**: `src/media_hygiene/cli/templates/mh.ps1.j2`, `src/media_hygiene/cli/templates/mh.sh.j2`, `src/media_hygiene/services/launcher_menu.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/{en,fr}/reference-troubleshooting.md`, `documentation/{en,fr}/commands/launcher.md`, `tests/unit/test_launcher_menu.py`

## Measured on Windows (2026-10-16, step 16 of mh-measure.ps1, PowerShell 5.1, Docker Desktop quit)

- `docker run` says, exit code 1:
  `failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine; check if the path is correct and if the daemon is running: open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified.`
- `docker version`: exit code 1 too (a cheap check before the run).
- Docker Desktop started again: answering after 5 s.

## Why

The likeliest error of a newcomer (maintainer, 2026-10-15): Docker Desktop not started, after a
reboot. Docker then prints its own message, in technical English (*error during connect … the
system cannot find the file specified*, the pipe of `dockerDesktopLinuxEngine`: exact text to
check), and the user does not know it is Docker Desktop to start. The tool itself cannot say it:
the container never starts.

## What to do

- In `mh` (both shells), after `docker run` fails (exit code not 0): ask the daemon with a quick
  `docker version --format '{{.Server.Version}}'` (PowerShell: output discarded, `$LASTEXITCODE`
  tested; bash: `>/dev/null 2>&1`). Only when that fails too, print one translated line:
  "Docker Desktop is not started: start it from the Start menu, wait for it to say it is
  running, then type the command again." (bash: "Docker is not started: …", without the Start
  menu). The check costs nothing when the run succeeds; the tool's own failures (exit 1, 2) are
  left as they are, since the daemon answers then.
- The menu run (`mh` alone, `mh menu` captured) goes through the same check: it says it once,
  and the menu asks nothing.
- Same for the `docker run` of `launcher` itself? It runs before `mh` exists: the guide's step 0
  says it in its "Docker Desktop not started?" line instead (troubleshooting page).
- The message goes through `menu_texts()` (`MenuTexts`, the messages of `mh` itself), checked
  free of `"`, `$`, backtick, backslash like the others.

## Acceptance

- Unit: the bash `mh` run with a fake `docker` whose `run` fails and `version` fails → the line,
  the exit code kept; `version` succeeds → no line; the PowerShell text holds the check, ASCII.
- Troubleshooting page, both languages: the Docker message (quoted from the maintainer's run)
  and the fix.

## Gain (estimated)

One cryptic error of the first day replaced by its fix in one sentence; no figure before the
maintainer's run.

## Decided (2026-10-15)

- Troubleshooting page, before the maintainer's run: describe the case (Docker's
  "error during connect…" when Docker Desktop is closed) and the fix, without quoting the exact
  message, marked "exact wording to check"; the maintainer completes the quote after the run.
  (Maintainer, in `/todo:iterate`.)
