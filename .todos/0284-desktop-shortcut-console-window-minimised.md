# 0284 — The desktop shortcut's PowerShell window invites closing it; the page says so too late

- **Priority**: Medium
- **Batch**: unassigned
- **Depends**: —
- **Files**: `src/media_hygiene/cli/templates/mh_windows.ps1.j2`, `src/media_hygiene/cli/templates/mh.ps1.j2`, `src/media_hygiene/cli/templates/mh_menu.ps1.j2`, `src/media_hygiene/review/templates/home_run.js.j2`, `src/media_hygiene/review/home_texts_run.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/commands/home.md`, `documentation/fr/commands/home.md`, `tests/unit/` (launcher templates, home page), `tests/measure/mh-measure.ps1`
- **Needs maintainer**: the choice between options A/B/C below, then a check on the Windows PC (desktop shortcut, Windows PowerShell 5.1, Avast running)

## Context

The maintainer double-clicked the desktop shortcut (2026-10-21): PowerShell opened, then the
home page. Thinking the console was noise once the page is there, they closed the PowerShell
window. The page kept working in appearance ("Nettoyer" showed `#clean`: same page, already
loaded, no request). Only when they started an audit did the "Media Hygiene est arrêté"
dialog appear. Logical (closing the window ends `docker run`, so the server), but confusing:
the user does not link the stop to the window closed a minute earlier.

## Constraint — the window is not only noise

Several home page steps run **in that window** (`home_texts_run.py`: "{command} runs in
{window}: answer it if it asks something", "Nothing moves? Look at {window} (Alt+Tab)"): the
`clean` confirmation, the console steps of `_mh_home`'s loop (`mh_menu.ps1.j2`). Hiding it
for good would leave those steps waiting on an invisible prompt. The audit, on the other
hand, runs in the page (`P.audit`, progress polled).

## Options (to decide)

- **A. Shortcut starts minimised** — `$link.WindowStyle = 7` in `_mh_shortcut` and
  `_mh_refresh` (WScript.Shell, no Add-Type: safe with Avast, see 0257 and the memory on it).
  The window sits in the taskbar; a step that needs it says "look at {window}" as today.
  Cheapest; the page's existing hints stay true. To check: whether a step's prompt flashes
  the taskbar button by itself (it does not restore the window).
- **B. A + bring the window back when a step needs it** — `(New-Object -ComObject
  WScript.Shell).AppActivate($PID)` before a console step. To check on 5.1: AppActivate may
  focus without restoring a minimised window; restoring needs `ShowWindow` (Add-Type
  user32 → Avast, refused).
- **C. Hidden window** (`-WindowStyle Hidden`) — rejected unless every console step moves to
  the page: the prompts above would be invisible, and the window flashes before hiding.

Whatever the option, two cheap changes regardless:

1. **The page notices the stop at once**: a light heartbeat (`/api/state` every few seconds,
   paused while the tab is hidden — `visibilitychange`) shows `#stoppedDlg` within seconds of
   the window closing, not at the next action. The dialog's text names the cause: "the
   PowerShell window of Media Hygiene was closed (or Ctrl+C)" + how to start again.
2. **The window says why it must stay open**: one line after the "Accueil prêt" line, e.g.
   "Keep this window open (minimised is fine): closing it stops Media Hygiene." In both
   languages (`_()`, `i18n_update`).

## Expected

1. Maintainer picks A or B (recommended: A + 1 + 2).
2. Shortcut (and the refresh of older shortcuts) written with the chosen window style, read
   back like the arguments are (0190 contract: one line, or why not).
3. Heartbeat in `home_run.js.j2` + reworded stopped dialog; unit tests on the rendered
   script and on the texts.
4. `documentation/{en,fr}/commands/home.md` say the window may be minimised, not closed;
   `docs_screenshots` to rerun (unasked).
5. A `mh-measure.ps1` step: shortcut started minimised, a console step from the page (does
   the prompt reach the user?), window closed → seconds until the page shows the dialog.
