# 0347 — Search by words gets "Sort by" and "Show" like the folders view

- **Priority**: Medium
- **Batch**: search
- **Depends**: —
- **Files**: `src/media_hygiene/search/templates/search.html.j2`, `src/media_hygiene/search/templates/search.js.j2`, `src/media_hygiene/search/templates/browse.html.j2`, `src/media_hygiene/search/templates/browse.js.j2`, `src/media_hygiene/search/app.py`, `src/media_hygiene/search/statements.py`, `src/media_hygiene/review/templates/pick_views.html.j2`

## Context

Reported by the maintainer (2026-10-24): the *Folders* view (`browse`) has *Sort by* (size …)
and *Show* (videos only …) at the top right (0301); the *Words* view has neither. Generic
features belong to both (memory: same features at the same place on every page; skill
`photo-picking-pages`).

## To do

- Move *Sort by* and *Show* into one shared template included by both pages at the same place.
- On search: *Show* filters before the limit (a SQL condition on the kind, like the years), *Sort
  by* adds size and date to *best match* (default) — the server sorts, so the first N shown
  are the right ones.
- Any other control only one of the two pages has: list it in the feedback, share it or say why
  not.

## Acceptance

- [ ] Search `Durbuy`, *Show: videos*, *Sort by: size*: the largest videos of Durbuy first.
- [ ] Both pages render the controls from the same include.
