# 0505 — Home page: run the short container steps in the page, their output in a popup

- **Priority**: High
- **Batch**: home
- **Depends**: 0504
- **Files**: `src/media_hygiene/cli/menu_entry.py`, `src/media_hygiene/review/templates/home_run.js.j2`, `src/media_hygiene/review/home_texts.py`, `src/media_hygiene/services/home_pages.py`, `src/media_hygiene/review/shared_routes.py`, `tests/unit/`, `documentation/en/commands/home.md`, `documentation/fr/commands/home.md`

## Reported (maintainer, 2026-10-30)

A step of the page should not say "go to your PowerShell window": the user wants to stay in
the browser.

## Today (read in `home_run.js.j2`, 2026-10-30)

A `Kind.CONSOLE` step ends the server (or runs beside it, `kept`, 0355): the page says
"switch to the window" (`T.runsConsole`, `T.switchNow`) and waits for it to come back.

## To do

1. The home page's server already runs in the container: it runs a short, non-interactive
   step itself (a new `Kind`, e.g. `INLINE`, or a flag), in a thread / subprocess with a time
   limit, and answers its console output (Rich rendered to text or HTML, no ANSI).
2. The page shows it in a dialog: running indicator, the output, Close; the page stays alive.
3. Candidates (to confirm one by one: no prompt, seconds): `config`, `backup`,
   `reports-prune {count}`, `people --forget`, `history`, `reports`. A step that asks
   (`restore`, `Risk.UNDO`) has its confirmation asked in the page first (existing
   confirm dialog), then runs with the flag that skips the console prompt.
4. One step at a time (a second click while one runs: refused, said).
5. Product rules: a save is shown by reading it back (e.g. `backup` names the zip found on
   disk); never a traceback in the dialog (the error message only); the one 👉 line.
6. Long steps (audit, clean) are out of scope: they have their own followed run or page.
7. Tests per candidate; docs EN + FR; `docs_screenshots` should run after.

## Outcome (2026-11-03) — PARTIAL

### Done

- `Step.inline` (catalog flag, `HomeAction.inline`): `config`, `backup`, `history`,
  `reports --prune {count}` run by the home server itself, whatever `mh` opened the page.
- `review/inline_step.py`, `POST /api/inline` (`RUN_PATHS`: home only, refused from a phone):
  `media-hygiene <words>` in a child process, `NO_COLOR`/`TERM=dumb`, 120 s limit
  (`INLINE_SECONDS`), ANSI stripped, a traceback cut to its last line, one at a time (409).
- `home_inline.js.j2`: the dialog (running, the output, Close), state reloaded after.
- Tests `tests/unit/test_inline_step.py`; docs EN + FR (`commands/home.md`); FR translations.

### Not done

- `people --forget` and `restore` (they prompt: need a "yes" flag skipping the console
  → code work, not the maintainer's: listed in 0718 (2026-11-12)
  question, asked in the page first). **Reason:** each CLI's prompt to read and flag; a
  follow-up of the same shape.
- `backup` names the zip it wrote (its own output); not re-read from disk by the page.
  → code work, not the maintainer's: listed in 0718 (2026-11-12)
- `docs_screenshots` should run (new dialog).
  → captures: one run of `docs_screenshots`, tracked in 0717 (2026-11-12)

## Closed by the inbox (2026-11-12)

Nothing left for the maintainer: each item above is answered (`→`); the code work left is
listed in 0718, the captures in 0717.
