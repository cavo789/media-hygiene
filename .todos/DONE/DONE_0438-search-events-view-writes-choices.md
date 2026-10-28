# 0438 — search *🗂 Events*: choices and rules write `sort-decisions.json` (2/4 of 0415)

- **Priority**: High
- **Batch**: search
- **Depends**: 0437
- **Files**: `src/media_hygiene/search/app.py`, `src/media_hygiene/search/templates/search.js.j2`, `src/media_hygiene/review/sort_now.py`, `src/media_hygiene/review/sort_rule.py`, `src/media_hygiene/review/sort_choices.py`, `src/media_hygiene/classify/page_overlay.py`, `documentation/en/commands/search.md`, `documentation/fr/commands/search.md`

## Why

Part 2 of 0415 (split 2026-10-27; design in `.todos/UNNEEDED/UNNEEDED_0415-*.md`): the choices
(M, R, rules) of review-sort, written in `sort-decisions.json` with the workbook value each saw
(`base`), conflicts never settled silently (`page_overlay`). Delete sets aside, as on every
tile page (skill `photo-picking-pages`).

**Decided (2026-10-28, inbox)**: Backspace takes back a choice once Delete has set it aside,
as in every tile page's large view.

## Explicit NON-goals

- Retiring review-sort (0439).

## Status — DONE (2026-10-28)

- Server: `search/events_choose.py` mounts every review-sort choice (`sort_choices.CHOICES`:
  event, files, forget, sure, destination, rule preview/save/remove) and *Sort this event now* at
  `/api/sort/…` on the Events view's session; `GET /api/sort/rules`, `/api/sort/progress`.
  `sort-decisions.json` written by the same session code (same format, `base` kept, conflicts
  from `page_overlay` unchanged). Each event tile carries its plan row and sort facts.
- Page: the card, Folder/Name fields, live destination, *Check, then sort*, *Remember as a rule*
  (the search's rule dialog in an event mode), *Your rules*, sure batch, runs — review-sort's
  scripts moved to `search/templates/events_*.js.j2`. Keys: Enter, F, E, N/P/U, O/S, Shift+S,
  V, Shift+Z, M, R, **T** (take back a choice made here); **Delete** sets aside, **⌫** takes
  the picked files back out (decided 2026-10-28).
- Checked in headless Chromium (mddoc-playwright, mocked API): tiles, destination, Enter save,
  T, S, R dialog, no page error.
