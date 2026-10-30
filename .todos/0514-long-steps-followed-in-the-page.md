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
