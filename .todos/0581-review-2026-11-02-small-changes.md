# 0581 — Review of the 2026-11-02 iterate: four small changes decided

- **Priority**: High
- **Batch**: review
- **Depends**: —
- **Files**: `src/media_hygiene/search/templates/search_events.js.j2`, `src/media_hygiene/search/folder_role_desk.py`, `src/media_hygiene/review/templates/`, `documentation/en/`, `documentation/fr/`

## Asked (maintainer, review of 2026-11-02)

Decided during the review of PR #58; the run stopped (usage limit) before they were made.

1. **0575, events found**: a row inside a folded group (e.g. folded *Not events*) is not shown,
   so *Confirm* never posts it and the button's count excludes it (rule: never act on hidden).
2. **0532, folder roles**: a protected folder overlapping an excluded one (either nested in the
   other) is refused with its reason, like the backup clash; `config.toml` unchanged.
3. **0520, burst contact sheet**: the page opens on the contact sheet when obvious series remain.
4. **0520**: the rows per screen follow the window height instead of a fixed 20 (a few rows at
   least). Load the `photo-picking-pages` skill.

## Tests

- 1: a folded row matching the filter is not posted; count matches what is posted.
- 2: protected inside excluded, excluded inside protected: both refused, file unchanged.
- 3–4: page test; check in headless Chromium (mocked API) as 0520 did.
- Docs en + fr where the behaviour is described; `docs_screenshots` to run afterwards.
