# 0285 — A console step started from the home page brings its PowerShell window forward, and the page says so at once

- **Priority**: Medium
- **Batch**: home
- **Depends**: 0284
- **Files**: `src/media_hygiene/cli/templates/mh_menu.ps1.j2`, `src/media_hygiene/review/templates/home_run.js.j2`, `src/media_hygiene/review/templates/home.js.j2`, `src/media_hygiene/review/home_texts_run.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/commands/home.md`, `documentation/fr/commands/home.md`, `tests/unit/test_launcher_home.py`, `tests/unit/test_home_given.py`, `tests/measure/mh-measure.ps1`

## Context

The maintainer (2026-10-21, after checking 0280 with step 14h): a step started from the home
page that asks in the console (`clean`'s "Proceed? y/n") is easy to miss: the browser stays in
front, the run dialog names the window, *Nothing moves? … (Alt+Tab)* comes only after 30 s
(`HINT_MS`); one waits and waits without switching to PowerShell.

Windows does not let a background process take the foreground from the active window (the
browser). Without run-time compilation (`Add-Type` user32 is refused: Avast, see 0257 and
0284), the most `mh` can do is `WScript.Shell.AppActivate`: depending on Windows'
foreground lock, the window comes forward or its taskbar button flashes (to check on the
maintainer's PC). A minimised window (0284 option A: the shortcut starts minimised) is not
restored by AppActivate (to check).

## Decided (maintainer, 2026-10-21)

**AppActivate + a page alert** (not the questions moved into the page: `mh` keeps asking in the
console before acting; not "keep as is").

## What to do

1. `mh_menu.ps1.j2` (`_mh_home`): before running a console step chosen on the page (not a page
   step: 0280 shows those in the tab), `$null = (New-Object -ComObject WScript.Shell).AppActivate($PID)`
   in a `try` (COM refused: nothing said). No `Add-Type`. `mh.sh.j2`: nothing (no portable way;
   say so in a comment).
2. The page (`home_run.js.j2` `openRun`, console steps only): the alert shown **at once**, large,
   instead of the 30 s hint: "⌨ {window} is waiting for your answer: switch to it (Alt+Tab, or
   its button in the taskbar)". The 30 s hint stays as the second nudge. Texts through `_()`,
   French translated.
3. `commands/home.md` (en + fr): a console step brings its window forward when Windows allows
   it, else its taskbar button flashes; the page says it at once.
4. Tests: the rendered PowerShell holds the AppActivate line before the console step, not before
   a page step; the page's console-step dialog shows the alert without waiting; ASCII kept.
5. A `mh-measure.ps1` step (or 14h extended): from the home page, Run on `clean`: did the window
   come forward, flash, or nothing? With the window normal, then minimised (0284).

## Acceptance

- Unit tests above pass; commit gate clean; `docs_screenshots` to rerun (the run dialog).
- The maintainer's answer to the measure step recorded here; if AppActivate does nothing on
  their PC, keep the page alert alone and say so in the docs.

## Status — PARTIAL (2026-10-21)

### Done
- `_mh_forward` (`mh_menu.ps1.j2`): before a console step chosen on the home page (menu step
  or form step, not a page command), `WScript.Shell.AppActivate($PID)`, then by the window's
  title (Windows Terminal owns its window), in a `try`; no `Add-Type` (tested).
- The run dialog of a console step shows at once, in bold, *Switch to {window} now (Alt+Tab, or
  its button in the taskbar): it may ask you something.* (`dlg-alert`); the 30 s hint stays.
  French translated gender-neutral ("mh peut vous y demander…": the window may be a terminal).
- `mh.sh.j2`: a comment only (no portable way for a terminal to come forward).
- Docs (en + fr) `commands/home.md`; tests in `test_launcher_home.py` (forward defined, page
  commands skipped, called once per call site) and `test_home_given.py` (alert for console
  steps only). Unit suite 2,492 passed; gate clean.
- `mh-measure.ps1` step 26 (26c bold line, 26d minimised, 26e normal window).

### Not done
- What AppActivate does on the maintainer's PC (forward, flashing button, nothing), window
  minimised and normal: `.\mh-measure.ps1 -Only 26 -Count 1`. If nothing on both, the page
  alert alone stays and the docs say so.
  **Reason:** Windows' foreground lock depends on the machine; not testable here.
- `docs_screenshots`: the run dialog changed.
