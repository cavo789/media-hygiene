# 0258 — Home page opened from a right-click names the folder; the "Running" popup says which window; step 10's questions match the page

- **Priority**: Medium
- **Batch**: launcher
- **Depends**: 0257
- **Files**: `src/media_hygiene/review/templates/home.html.j2`, `src/media_hygiene/services/home.py`, `src/media_hygiene/cli/templates/mh.ps1.j2`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/commands/home.md`, `documentation/fr/commands/home.md`, `tests/measure/mh-measure.ps1`

## Context

Seen by the maintainer on 2026-10-19 (mh-measure step 10c, with the home page of 0210):

- A right-click on `L'ete 2019` opens the home page, but nothing on it says that folder is part of
  this session: "Am I supposed to see 'L'ete 2019' somewhere?" The console menu of before said it
  ("The step chosen also analyses: …"). The audit does count it (40 → 43 files).
- After a *Run*, the popup says "Running in the window where mh runs: this page comes back when it
  ends." — the maintainer did not know which window, nor whether to wait; the PowerShell window is
  often behind the browser.
- Step 10c still asks about "the mh menu" and "type 1": since 0210 it is a page and a *Run* button.

## What to do

1. The page knows the folders given with `--photos` (the launcher relays them, as it relays the
   steps): *Where you are* says "This page also analyses: C:\…\L'ete 2019" (one line per folder),
   and the steps it runs get them (already so, 0181).
2. The popup after *Run*: "mh audit runs in the PowerShell window of mh (taskbar): this page comes
   back by itself when it ends." — plus, after 30 s without the page ending, a hint "Nothing
   moves? Look at the PowerShell window (Alt+Tab)."
3. mh-measure step 10c: questions rewritten for the page (the page opens; *Where you are* names
   the folder; *Run* on `mh audit`, the audit runs in the PowerShell window with 43 files).
4. Docs en + fr (home page), French translations.

## Acceptance

- Tests: the page renders the folder line when the relay gives folders, none otherwise; the popup
  wording; ASCII of the rendered mh.ps1.
- The maintainer's step 10 reads without guessing (after 0257).

## Gain

A right-click that visibly applies to the folder clicked, and a *Run* that says where it runs —
two questions the maintainer could not answer from the page (measured: step 10, 2026-10-19).

## Status — PARTIAL (2026-10-19)

### Done
- `mh.ps1` gives a relayed page (`home`, `browse`) the host folders of `--photos` in
  `MEDIA_HYGIENE_LAUNCHER_PHOTOS` (`|` between them; never carried into suggested commands);
  `home_state` turns them into `HomeState.given`; the page draws them first under *Where you
  are*, in bold: *This page also analyses: C:\…\L'ete 2019*, one line per folder.
- The popup after *Run*: *mh audit runs in the PowerShell window of mh (in the taskbar): this
  page comes back by itself when it ends* (*the terminal where mh runs* from `mh.sh`); after
  30 s without the page coming back, *Nothing moves? Look at the PowerShell window of mh (in the
  taskbar) (Alt+Tab).*
- French translations; docs EN/FR `commands/home.md`, `commands/launcher.md` (`mh --photos`
  alone); tests `tests/unit/test_home_given.py` (relay line, ASCII, folder lines or none, not
  carried, popup wording per shell, the 30 s hint, French).
- `mh-measure.ps1` step 10c rewritten for the page: the page opens; *Where you are* names the
  folder; *Run* on `mh audit` names the window, then the 30 s hint; the files scanned (43
  expected); the page back after the audit; the background right-click names the folder.

### Not done
- `mh.sh` does not relay the folders (the right-click is Windows only; `mh --photos X` alone in
  bash opens the page without the line). File a TODO if wanted.
  → keep: Windows only (review of feedback 2026-10-19-3, 2026-10-20).
- The maintainer's step 10 reading without guessing.
  **Reason:** needs Windows; same command as 0257, fetched at 8fefa13ff2096fc44972ecfca7734aae3acb60bc (`-Only 10`, after a reboot).
- Captures of `commands/home.md` / `commands/launcher.md` are stale: `docs_screenshots` should
  run (not run here: heavy).
