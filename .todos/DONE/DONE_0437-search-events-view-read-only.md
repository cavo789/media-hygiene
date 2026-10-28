# 0437 — search: an *🗂 Events* view, read-only (1/4 of 0415)

- **Priority**: High
- **Batch**: search
- **Depends**: —
- **Files**: `src/media_hygiene/search/app.py`, `src/media_hygiene/search/templates/search.html.j2`, `src/media_hygiene/search/templates/search.js.j2`, `src/media_hygiene/review/templates/pick_views.html.j2`, `src/media_hygiene/review/sort_views.py`, `src/media_hygiene/review/sort_session.py`, `documentation/en/commands/search.md`, `documentation/fr/commands/search.md`

## Why

0415 (too big for one run: review-sort is ~2 200 lines, measured `wc -l`) split by the
maintainer on 2026-10-27 into 0437–0440. Read `.todos/UNNEEDED/UNNEEDED_0415-*.md` for the whole
design. This part: the events of a classify plan shown in search, read-only: the list, its
filters, an event's card, the progress. No choice written yet.

## Explicit NON-goals

- Choices, rules, Delete (0438); retiring review-sort (0439); browse templates (0440).

## Status — DONE (2026-10-28)

- `search/events_desk.py`: `GET /api/events` (state + progress), `GET /api/events/<id>` (card +
  the photos as the search's own tiles, by index key: previews, large view, set aside unchanged);
  the plan read on the first ask (`open_sort_review`), never at search start.
- Page: *🗂 Events of the latest classify* in the left column (`search_events.*.j2`): progress
  line, review-sort's three filters (kept per viewer), ✓ sorted / ⚠ conflict, the card (name,
  folder, why); `/events` opens it.
- Not checked in headless Chromium (mddoc-playwright) in this run.
