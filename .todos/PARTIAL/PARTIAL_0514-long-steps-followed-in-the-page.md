# 0514 — Long steps (audit, clean, import, classify, sort, undo, purge, apply) run and followed in the page

- **Priority**: High
- **Batch**: one-interface
- **Depends**: 0505 (the in-page runner and its dialog)
- **Files**: `src/media_hygiene/console/` (progress facade), `src/media_hygiene/review/templates/home_run.js.j2`, `src/media_hygiene/review/home_texts_run.py`, `src/media_hygiene/services/home_pages.py`, `src/media_hygiene/cli/menu_entry.py`, `tests/unit/`, `documentation/en/commands/home.md`, `documentation/fr/commands/home.md`

## Why

Part 3 of 0513 (one interface). Today these `Kind.CONSOLE` steps send the user to PowerShell
(`T.runsConsole`); 0505 covers short steps only (its point 6 leaves the long ones out).

## To do

1. The home server runs the step in the container (a subprocess of `media-hygiene`, one at a
   time), its progress (the `console/` progress bars) sent to the page as events (polling a
   route, as the page already does; no new dependency).
2. A run panel: the stage, the bar, files/s, Stop (the step's own clean stop: a `clean`
   stopped halfway leaves its journal consistent, as Ctrl+C does today — test it), then the
   summary and the one 👉 line, the report's link.
3. Questions (`clean`'s "Continue?", `undo`, `purge`): asked in the page's confirm dialog
   first, then the step runs with the flag that skips the console prompt; the risk wording
   (🔒 / undo line) the same as in the console.
4. The tab closed or reloaded: the run goes on; reopening the page shows it again (question
   in 0513 for the maintainer).
5. Never a traceback in the panel; an error says its message and the console command to
   retry.
6. Tests: one per step (fake runner), Stop, a question answered No; docs EN + FR,
   `docs_screenshots` after.

## Where the user gains

Before: 8 everyday steps, the heaviest ones, are run and followed in PowerShell. After: in
the page, with the same progress and the same questions.

## Status — PARTIAL (2026-11-03)

### Done

- Point 2 (part): the follow dialog of a console step `mh` runs beside the server shows the
  stage title, a `<progress>` bar, done / total, files a second (from two polls) and the file
  (`showProgress`, `home_run.js.j2`).
- Point 4: the tab closed or reloaded, the step goes on in `mh`'s window; the page, opened
  again, finds it on `GET /api/step` and follows it again (`resumeStep`, `home_inline.js.j2`).
- Tests `tests/unit/test_step_resume.py`; docs EN + FR (`commands/home.md`); FR translations.

### Not done

- Points 1, 2 (Stop), 3, 5: run the long steps in the home container itself, a Stop button,
  the questions asked in the page then `--yes`, the summary and 👉 line in the panel.
  **Reason:** the home server's container mounts the photos read-only and the writing steps
  run in a container of their own started by `mh.ps1` (`step_progress.py`, `mh.ps1.j2` `:ro`
  mode per command) — a mounts design the maintainer chose. Running `clean` from the page
  means either the home container gets read-write mounts (loses: the read-only guarantee of
  every page) or `mh.ps1` runs the step detached with its output and a stop file shared through
  the reports folder (PowerShell 5.1, to measure on Windows). **Needs maintainer**: which way.
- Point 3 also drops `mh`'s second question before acting (the page's confirm would replace
  it): a safety design choice to confirm first.
- `docs_screenshots` should run (follow dialog changed).

## Decided (2026-11-03, review of PR #61)

By the maintainer: (1) the writing steps run from the page through `mh.ps1` in the background (the home container stays read-only); (2) the page's confirmation replaces mh's second console question. Remainder filed as 0586.
