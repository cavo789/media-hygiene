# 0365 — The home server restarted once after a crash; its audit with the settings of now

- **Priority**: High
- **Batch**: home
- **Depends**: 0355, 0358
- **Files**: `src/media_hygiene/cli/templates/mh_menu.ps1.j2`, `src/media_hygiene/cli/templates/mh.sh.j2`, `src/media_hygiene/constants.py`, `src/media_hygiene/cli/unexpected.py`, `src/media_hygiene/cli/cmd_home.py`, `src/media_hygiene/cli/home_audit.py`, `tests/unit/test_launcher_home.py`, `tests/integration/test_home_audit.py`, `tests/measure/mh-measure.ps1`

## Context

Review of the feedback of 2026-10-24 (maintainer, 2026-10-25: *one TODO for both*), two items
left by the PARTIAL TODOs:

- **0355**: the home server runs in the background for the whole session; when it crashes (an
  error the tool did not foresee, a native library, memory), `mh`'s loop gives the prompt back,
  and the user must type `mh` again. Telling a crash from an exit of the tool is not possible
  today: exit code 1 is also a user error (`ExitCode`, `constants.py`).
- **0358**: the audit run from the home page (`page_audit(runtime)`, `cli/home_audit.py`) is
  bound to the runtime of the start: a setting changed during the session (an exclusion, the
  workers) is not used by it until `mh` starts again.

## What to do

1. An exit code of its own for an unexpected end of the server (`ExitCode.CRASHED`, below the
   step range and the signals; `test_the_step_range_never_reaches_a_signal_s_code` extended),
   given by the handler of unexpected errors (`cli/unexpected.py`) for `home` only.
2. `mh.ps1` / `mh.sh`: that code → one line (*The home page stopped unexpectedly: started
   again.*), the server started again once; a second crash within a minute ends the loop with
   the line and the issue link the tool already prints. A container killed by Docker (137, out
   of memory) counts as a crash too; Ctrl+C (130) never does.
3. The home page's audit takes the runtime of now (`FreshRuntime`, as the page's state since
   0358): `page_audit(fresh.runtime)`.
4. Tests: the bash loop with the fake docker (a crash restarts once, two crashes end; Ctrl+C
   ends); the PowerShell block as text; the audit uses an exclusion added after the start.
5. A step of `mh-measure.ps1` (Windows only): `docker kill` the home server's container, the
   page comes back by itself (timed with Docker's events, as step 35d).

## Acceptance

- The home server killed during a session: the page is back within a few seconds without
  typing anything; killed twice in a row: the prompt back, with the reason.
- An exclusion added to `config.toml` during the session is used by the next audit run from the
  page.

## Gain

A crash no longer ends the session (today: type `mh` again, 4.8–5.6 s plus the user noticing,
*measured* 35d / *estimated*); no stale settings in the page's audit.

## Status — PARTIAL (2026-10-26)

Done: `ExitCode.CRASHED` (5, `home` only, from `cli/unexpected.py`) and `ExitCode.KILLED`
(137); `mh.sh` / `mh.ps1` restart the server once, a second crash within `CRASH_WINDOW` (60 s)
ends the loop with its line; Ctrl+C (130) unchanged; the page's audit reads the settings of now
(`page_audit(FreshRuntime)`); tests (bash fake docker, PowerShell text, audit exclusion, exit
code); docs en + fr.

Left: item 5, the `mh-measure.ps1` step (`docker kill` the home container, timed with Docker's
events) — Windows only, for the maintainer.
