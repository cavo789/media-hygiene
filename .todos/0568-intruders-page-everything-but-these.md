# 0568 — Intruder files page: "everything but these extensions"

- **Priority**: Low
- **Batch**: clean
- **Depends**: —
- **Files**: `src/media_hygiene/services/intruder_pick.py`, `src/media_hygiene/services/intruders_reviewing.py`, `src/media_hygiene/review/templates/intruders_review.html.j2`, `src/media_hygiene/review/templates/intruders_review.js.j2`, `documentation/en/`, `documentation/fr/`

## Why

Question of 0410 **fichiers intrus dans les dossiers photos** (review of
`feedback-2026-10-27-iterate.md`, 2026-11-02). Today the user ticks each extension to quarantine.
With many types, it is faster to tick the few to keep. Maintainer: add it.

## What

- One switch on the page: *Set these aside* ↔ *Set everything aside but these*. Before *Apply*,
  the page names the extensions concerned and the count of files (seeing first: nothing
  leaves by surprise).
- Test: 4 extensions, 1 kept, gives the 3 others set aside.
- Docs en + fr; `docs_screenshots` should run.
