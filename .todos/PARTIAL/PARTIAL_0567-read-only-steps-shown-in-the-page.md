# 0567 — Home page: status, folders, reports, inventory, config shown in the page

- **Priority**: Medium
- **Batch**: home
- **Depends**: —
- **Files**: `src/media_hygiene/services/home.py`, `src/media_hygiene/services/home_pages.py`, `src/media_hygiene/services/status.py`, `src/media_hygiene/services/history_here.py`, `src/media_hygiene/review/templates/home.html.j2`, `documentation/en/`, `documentation/fr/`

## Why

Question of 0350 **l'historique des runs affiché dans la page** (review of
`feedback-2026-10-27-iterate.md`, 2026-11-02). These read-only 🔒 steps still print their result
in the terminal only when started from the home page. Rule *visible in the web or nonexistent*.
Maintainer: yes.

## What

- `status`, `folders`, `reports`, `inventory` (its summary) and `config` (show) answer in the page,
  in a dialog or panel, like the history (0350), from the same service as the console.
- The console output is unchanged when typed.
- Docs en + fr; `docs_screenshots` should run.

## Status — PARTIAL (2026-11-03)

### Done
- `status`, `reports`, `inventory`, `config` chosen on the home page open `/console/<step>/`
  (`services/console_here.py`, `cli/page_capture.py`): the same command function runs with a
  recording console, its text shown in a page (🔒 line, bar, docs link); typed in a terminal,
  unchanged. Tests `tests/unit/test_console_here.py`. Docs en + fr (each command page, *With mh*).

### Not done
- `folders`: a host step (`Kind.HOST`, run by `mh.ps1` on Windows), the container cannot list it.
  **Reason:** needs `mh.ps1` to hand its listing to the server — a design of its own.
- The text is shown preformatted (Rich's plain export), not as a styled panel/table.
  **Reason:** one source for console and page was preferred; styling per step is a follow-up.
- `docs_screenshots` should run (new pages).
