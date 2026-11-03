# 0586 — Writing steps (audit, clean, import, sort, undo, purge) started from the page, run by `mh.ps1` in the background

- **Priority**: High
- **Batch**: launcher
- **Depends**: 0514 (PARTIAL: steps followed in the page, resumed after the tab closed)
- **Files**: `src/media_hygiene/cli/templates/mh.ps1.j2`, `src/media_hygiene/cli/templates/mh_menu.ps1.j2`, `src/media_hygiene/cli/templates/mh.sh.j2`, `src/media_hygiene/review/templates/home_run.js.j2`, `src/media_hygiene/review/step_watch.py`, `tests/unit/`, `tests/measure/mh-measure.ps1`
- **Needs maintainer**: a run on Windows PowerShell 5.1 + Docker Desktop (with Avast) of the new path, as a step of `mh-measure.ps1`

## Decided (maintainer, 2026-11-03, review of PR #61)

- The home server's container stays **read-only** on the photos. A writing step chosen on the
  page is run by `mh.ps1` in the background (its own container, as today), its output and a stop
  file shared through the reports folder; the page follows it (0514) and offers **Stop**.
- The page's confirmation (count of files, the undo line) **replaces** mh's second question in
  the console: the step is started with `--yes` once confirmed in the page.
- The step goes on when the tab is closed; the console stays a full interface (0513).

## Acceptance

- [ ] `audit`, `clean`, `import` started and stopped from the page, the console not needed
- [ ] One confirmation, in the page; the undo line shown at the end
- [ ] Measured on Windows (step of `mh-measure.ps1`), no Avast alert
