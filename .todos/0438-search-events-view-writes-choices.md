# 0438 — search *🗂 Events*: choices and rules write `sort-decisions.json` (2/4 of 0415)

- **Priority**: High
- **Batch**: search
- **Depends**: 0437
- **Files**: `src/media_hygiene/search/app.py`, `src/media_hygiene/search/templates/search.js.j2`, `src/media_hygiene/review/sort_now.py`, `src/media_hygiene/review/sort_rule.py`, `src/media_hygiene/review/sort_choices.py`, `src/media_hygiene/classify/page_overlay.py`, `documentation/en/commands/search.md`, `documentation/fr/commands/search.md`
- **Needs maintainer**: which key takes back a choice once Delete sets aside (asked at the start of the run)

## Why

Part 2 of 0415 (split 2026-10-27; design in `.todos/UNNEEDED/UNNEEDED_0415-*.md`): the choices
(M, R, rules) of review-sort, written in `sort-decisions.json` with the workbook value each saw
(`base`), conflicts never settled silently (`page_overlay`). Delete sets aside, as on every
tile page (skill `photo-picking-pages`).

## Explicit NON-goals

- Retiring review-sort (0439).
