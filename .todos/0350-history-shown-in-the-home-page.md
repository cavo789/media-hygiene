# 0350 — The home page shows the history of runs in the page, not only in the terminal

- **Priority**: medium
- **Batch**: unassigned
- **Depends**: —
- **Files**: `src/media_hygiene/review/home_app.py`, `src/media_hygiene/review/home_step.py`, `src/media_hygiene/review/templates/`, `src/media_hygiene/cli/cmd_history.py`, `src/media_hygiene/actions/runs.py`, `src/media_hygiene/cli/menu_catalog_clean.py`, `documentation/en/commands/history.md`, `documentation/fr/commands/history.md`

## Context

Reported by the maintainer (2026-10-24): on the home page, *History and undo* → **4 See what
each run did** (`history`, `menu_catalog_clean.py`), they clicked and waited… and nothing came in
the page: the table was printed in the PowerShell window only. `POST /api/step` ends the home
server with `STEP_EXIT_BASE + n` and `mh` runs `history` in the terminal (`home_step.py`), so the
browser tab is left as it was, with no sign of where the answer went. Someone who chose the
action in the page expects the answer in the page. `history` is read-only (🔒) and its data are
already a list of `RunSummary` (`actions/runs.py`: `list_run_ids` + `summarize`), so the page can
show it itself, without leaving the server.

## To do

- `GET /api/history` on the home server (read-only, same `/journal` checks as `cmd_history`:
  no journal mount → the same message and hint, in the page) returns the runs: id, command/kind,
  date, files deleted, space freed, moves, restores, whether it can still be undone.
- The *History and undo* space shows them as a table in the page when **See what each run did**
  is chosen (no `POST /api/step`): the backup 🛟 and phone 📱 notes when they apply, and each
  run's undo as the one-liner to copy (`mh undo <run>`), the undo line of the CLI. Same header
  and way back home as every page (`same-features-on-tile-pages`).
- Share the table's facts between the terminal and the page (one function building the rows),
  so both say the same thing.
- List the other 🔒 steps that only print in the terminal when started from the page (e.g.
  `status`, `folders`, `reports`): note them in the feedback for a follow-up TODO — do not
  widen this one.
- Documentation (en + fr) of `history`: it can be seen from the home page too.

## Acceptance

- [ ] Clicking **See what each run did** on the home page shows the runs in the page, with the
      same figures as `mh history` in the terminal (test on a journal with a clean, an undo, a
      backup and a phone run).
- [ ] Without a journal mount, the page shows the message and hint of `cmd_history`, never a
      traceback.
- [ ] Nothing is printed in the terminal and the home server keeps running.
- [ ] `docs_screenshots` to run (home page, history page captures).
