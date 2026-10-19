# 0257 — The shortcut and the right-click start `mh` without `-ExecutionPolicy Bypass`: Avast blocks it

- **Priority**: High — the maintainer: "we cannot accept that a user has to create an exception"
- **Batch**: launcher
- **Depends**: —
- **Files**: `src/media_hygiene/cli/templates/mh_windows.ps1.j2`, `src/media_hygiene/services/launcher_host.py`, `tests/unit/test_launcher_host.py`, `documentation/en/commands/launcher.md`, `documentation/fr/commands/launcher.md`, `documentation/en/reference-troubleshooting.md`, `documentation/fr/reference-troubleshooting.md`, `tests/measure/mh-measure.ps1`

## Context

Measured on the maintainer's PC on 2026-10-19 (mh-measure step 10, `measures-20261019-2208`, image
47a411fa built from main a21f880):

- A right-click on a folder starts
  `powershell.exe -NoExit -ExecutionPolicy Bypass -Command ". '<mh.ps1>'; mh --from-explorer #" "%V"`
  (`_mh_start` in `mh_windows.ps1.j2`, the same line for the Desktop shortcut). Avast's Behavior
  Shield blocked that `mh.ps1` (**IDP.HELU.PSD11**, process `powershell.exe`, 20:09:52Z): the home
  page container had started ("Home page ready"), but the PowerShell side was stopped. A *Run* on
  the page then ended the page (exit code 101, seen in Docker's events) and nothing ran the step:
  it looked like a bug of the home loop (21:45 and 22:09, twice).
- Same detection name as on 2026-10-16 (memory of the sessions): a `powershell -ExecutionPolicy
  Bypass` started from a temp folder. A user-like run (`. mh.ps1` in a normal console, step 11)
  raised nothing the same evening.
- After a detection, Avast refuses new files at that path until a reboot: `mh shortcut` could not
  write `Media Hygiene.lnk` ("Access refused") all evening.
- Earlier the same evening, the maintainer's own right-click (published mh, `mh.ps1` under
  `%USERPROFILE%\media-hygiene`, also with Bypass) opened without an alert: the folder (temp) or the
  new behaviour of `mh.ps1` (`Get-Process`, `docker ps`, `wsl.exe` of 0250/0252) may weigh too —
  **to tell apart** by the measure below.
- Every `mh` user already sets `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` (step 1 of
  the docs, quick guides): `. mh.ps1` of a file written on the PC is allowed without Bypass.

The maintainer (2026-10-19): the antivirus must not react; an exception is not acceptable.

## What to do

1. `_mh_start`: drop `-ExecutionPolicy Bypass` (keep `-NoExit -Command ". '<file>'; mh …"`). When
   the policy refuses the file (Restricted), the window says the one line to type
   (`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`) instead of PowerShell's raw error: a
   `try { . '<file>' } catch { … }` in the command, ASCII, PowerShell 5.1.
2. Existing shortcuts and right-click entries keep the old line until rewritten: `mh update` (or
   the next `launcher`) rewrites them when they exist (read back, said in one line), so users get
   the fix without retyping `mh shortcut` / `mh explorer`.
3. Look for any other `Bypass`, `-EncodedCommand`, `Invoke-Expression`, `Add-Type`, hidden window
   or `conhost` start in the launcher templates: none should remain (test: the rendered scripts
   contain none of them).
4. mh-measure step 10: ask, after the right-click, whether Avast (or Windows Defender) showed
   anything, and log the shortcut/registry command; a variant with `mh.ps1` under
   `%USERPROFILE%\media-hygiene` (the real place) vs under `-Work` to tell the path's weight.
5. Docs en + fr: launcher page (what the shortcut starts), troubleshooting (an antivirus blocked
   `mh.ps1`: what it means, `mh update`, never "add an exception" as the advice).

## Acceptance

- Unit tests: no `Bypass` in the rendered `mh.ps1`; the refused-policy line rendered; ASCII.
- The maintainer's step 10 after a reboot (Avast's path lock lifted): right-click → page → *Run*
  `mh audit` runs in the window, **no Avast alert**; then 0250's check (close with the X, next
  right-click stops the leftover).

## Gain

The shortcut and the right-click usable on a PC with Avast (measured: blocked twice the same
evening) without any exception.
