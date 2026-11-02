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
