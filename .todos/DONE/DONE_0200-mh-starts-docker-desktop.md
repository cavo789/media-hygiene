# 0200 — `mh`: start Docker Desktop itself when it is not running

- **Priority**: High — the likeliest error of a newcomer (0174) becomes nothing to do
- **Batch**: launcher
- **Depends**: —
- **Files**: `src/media_hygiene/cli/templates/mh.ps1.j2`, `src/media_hygiene/services/launcher_menu.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/unit/test_launcher_docker_down.py`, `documentation/en/reference-troubleshooting.md`, `documentation/fr/reference-troubleshooting.md`, `documentation/en/commands/launcher.md`, `documentation/fr/commands/launcher.md`, `tests/measure/mh-measure.ps1`

## Context

Chosen by the maintainer on 2026-10-17 (proposal A3). 0174 (DONE) made `mh` say "Docker Desktop is
not started: start it from the Start menu…" after a failed run. After a reboot, the Media Hygiene
shortcut (0180) therefore fails until the user finds Docker Desktop and starts it.

Docker Desktop has its own command line (checked on 2026-10-17 in Docker's reference):
`docker desktop start` waits for the operation to complete unless `--detach`, and `--timeout`
ends it with a non-zero exit code; `docker desktop status` exists too. Since which Docker Desktop
version: to check (an older version answers that `desktop` is not a docker command).

## What to do

- **`mh` alone (the menu, the shortcut, the right-click entry)**: before reading the menu, check
  the daemon (`docker version`, output discarded, as 0174). Down: one line "Docker Desktop is not
  started: starting it (up to 3 minutes)…", `docker desktop start --timeout 180`, then
  `docker version` again; it answers: the menu shows as usual. Measure the cost of that check in
  step 16 (it runs once per menu, not per command).
- **Any other command** keeps 0174's check after a failed run (no cost when Docker runs). When the
  daemon is down: start Docker Desktop as above, then say "Docker Desktop is ready: type the
  command again (↑ then Enter)". Never run a command a second time by itself: 0174's check cannot
  tell a daemon that was down from one that stopped in the middle of a `clean`.
- `docker desktop start` unknown (an old version), failed, or timed out: today's message, the exit
  code kept.
- The wait (180 s) is a constant next to `BROWSE_WAIT` in `launcher_menu.py`, not a setting: it
  covers a cold start (to confirm with step 16's timing).
- Step 16 of `mh-measure.ps1`: after recording 0174's message, run `mh` alone with Docker Desktop
  quit and record the time until the menu shows; then quit Docker Desktop again and run
  `mh history`: the "type the command again" line.

## Explicit non-goals

- The bash `mh` (Linux, WSL): Docker Engine is a service and `mh` never runs `sudo`; its message
  stays.
- No check before every command (0174 chose a check after a failure, free when Docker runs).

## Acceptance

- Unit (`test_launcher_docker_down.py`): the rendered `mh.ps1` holds
  `docker desktop start --timeout 180`, both messages, ASCII; the menu path checks first and goes
  on after a successful start; another command never runs twice (text checks, as the other
  PowerShell tests).
- Docs both languages: troubleshooting ("Docker Desktop is not started" now starts it, and what to
  do when that fails), launcher page.
- Windows (maintainer, after the work; closes the TODO, implementing needs no maintainer — inbox 2026-10-19): one run on Windows: step 16 of `mh-measure.ps1`, extended (Docker Desktop quit, then `mh` alone, then `mh audit`).

## Gain (estimated)

After a reboot, double-clicking Media Hygiene: an error, then finding Docker Desktop in the Start
menu, waiting, typing again → the menu shows once Docker Desktop has started (≈ 20–60 s,
estimated from step 16 of 2026-10-16, where Docker Desktop answered 5 s after being started by
hand; a cold start is longer: to measure), nothing to do.

## Status — DONE (2026-10-19)

### Done
- `mh.ps1`: `mh` alone and `mh menu` (so the shortcut and the right-click entry) ask `docker version`
  first and, when it does not answer, say "Docker Desktop is not started: starting it (up to 3
  minutes)…", run `docker desktop start --timeout 180`, then `docker version` again; the page or the
  menu follows on success (`templates/mh_desktop.ps1.j2`: `_mh_desktop`, `_mh_start`).
- Any other command keeps 0174's check after a failed run; Docker down: started the same way, then
  "Docker Desktop is ready: type the command again (↑ then Enter)"; the command is never run twice,
  the run's exit code is kept. Unknown subcommand, failure or timeout: 0174's line, as before.
- `DESKTOP_WAIT = 180` next to `BROWSE_WAIT` (`launcher_menu.py`), not a setting. Bash `mh` unchanged.
- Tests (`test_launcher_docker_down.py`): the command, both messages, ASCII, the check before the
  page and the menu, never a second `docker run` after a failure; French translated.
- Docs both languages: troubleshooting ("Docker answers instead of the tool": mh starts it, what to
  do when it cannot), launcher page ("What mh does for each command").
- Step 16 of `mh-measure.ps1` extended: after 0174's message, `_mh_desktop` timed (what `mh` alone
  runs before the page), then a second quit and `mh audit`: the "type the command again" line, the
  audit typed again.

### Not done
- The Windows run (maintainer): image built from branch `iterate/2026-10-19`, then
  ```powershell
  cd C:\temp
  Invoke-WebRequest https://raw.githubusercontent.com/cavo789/media-hygiene/iterate/2026-10-19/tests/measure/mh-measure.ps1 -OutFile .\mh-measure.ps1
  Unblock-File .\mh-measure.ps1
  .\mh-measure.ps1 -Only 16 -Count 20
  ```
  It gives the cold-start time (16c) that confirms or changes the 180 s, and whether `docker desktop
  start` exists in the maintainer's Docker Desktop version (16 logs the client version).
  **Reason:** needs Windows + Docker Desktop.
- No documentation capture is stale (no console capture shows these lines).

### Measured (2026-10-19, step 16, Docker Desktop client 29.8.2, image a90d9b43)
- 16a/16b: with Docker Desktop quit, `docker run` says *failed to connect to the docker API at
  npipe:////./pipe/dockerDesktopLinuxEngine … The system cannot find the file specified.*, exit 1;
  `docker version` exit 1.
- 16c/16d: **mh did not start Docker Desktop.** Two PowerShell functions were named `_mh_start`
  (this TODO's, and the Explorer entry's command line in `mh_windows.ps1.j2`); the second replaced
  the first: `mh` printed `powershell.exe -NoExit …`, took it for "answering" after 0 s, and after a
  failed `mh audit` said "Docker Desktop is ready" while it was not. Fixed: renamed
  `_mh_desktop_start`, and a test fails on any function defined twice in `mh.ps1` / `mh.sh`.
- Step 16 again with the fix (image 8d6b603e): `mh` alone started Docker Desktop, answering after
  **11 s**; after a failed `mh audit`, started it in 9 s and said "type the command again"; typed
  again: exit 0. The 180 s limit leaves a wide margin: no setting needed.
