# 0459 — search: a *shortest first* sort for videos

- **Priority**: Low
- **Batch**: search
- **Depends**: —
- **Files**: `src/media_hygiene/search/query.py`, `src/media_hygiene/search/templates/`, `documentation/en/commands/search.md`, `documentation/fr/commands/search.md`

## Why

The maintainer, 2026-10-29 (inbox, 0446 question 3): to find the failed 1–2 s videos, a sort
rather than a new filter. The 3 s red badge stays a named constant (question 6).

## Acceptance

- A *Shortest first* sort in search orders videos by duration (photos after); test on the index.
- Docs en + fr.
