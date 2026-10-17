# 0200 — `mh`: start Docker Desktop itself when it is not running

- **Priority**: High — the likeliest error of a newcomer (0174) becomes nothing to do
- **Batch**: launcher
- **Depends**: —
- **Files**: `src/media_hygiene/cli/templates/mh.ps1.j2`, `src/media_hygiene/services/launcher_menu.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/unit/test_launcher_docker_down.py`, `documentation/en/reference-troubleshooting.md`, `documentation/fr/reference-troubleshooting.md`, `documentation/en/commands/launcher.md`, `documentation/fr/commands/launcher.md`, `tests/measure/mh-measure.ps1`
- **Needs maintainer**: after the work, one run on Windows: step 16 of `mh-measure.ps1`, extended (Docker Desktop quit, then `mh` alone, then `mh audit`)

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
- Windows (maintainer): step 16 extended.

## Gain (estimated)

After a reboot, double-clicking Media Hygiene: an error, then finding Docker Desktop in the Start
menu, waiting, typing again → the menu shows once Docker Desktop has started (≈ 20–60 s,
estimated from step 16 of 2026-10-16, where Docker Desktop answered 5 s after being started by
hand; a cold start is longer: to measure), nothing to do.
