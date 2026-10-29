# 0483 — Home page layout: compact next step, audit moved to the Clean stage

- **Priority**: Medium
- **Batch**: home
- **Depends**: —
- **Files**: `src/media_hygiene/review/templates/home.html.j2`, `src/media_hygiene/review/templates/home_draw.js.j2`, `src/media_hygiene/review/templates/home_parts.css.j2`, `src/media_hygiene/cli/home_state.py`, `src/media_hygiene/cli/home_audit.py`, `src/media_hygiene/cli/home_cycle.py`, `documentation/en/`, `documentation/fr/`

Maintainer feedback (2026-10-29): in three weeks of use, the "next step" hero was never clicked;
the maintainer goes straight to Clean, Sort and mostly Search. The "photo cycle" block is liked
and stays as is.

New order, top to bottom: cycle → favourites (separate TODO) → next step → random photos
(separate TODO) → "where you are" tiles → recent reports.

- The next step is no longer a hero: one compact line or card (it stays, it teaches).
- "Audit in this page" leaves the home page: the audit runs from the *Clean* stage of the cycle
  (still in-page, same run view) and can be added to favourites.
- Both languages of the home documentation; `docs_screenshots` to run afterwards (not unasked).
