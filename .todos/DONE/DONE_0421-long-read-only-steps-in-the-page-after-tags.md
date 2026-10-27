# 0421 — Long read-only steps run in the page: faces, inventory, phone import after `tags`

- **Priority**: Medium
- **Batch**: home
- **Depends**: —
- **Files**: `src/media_hygiene/review/home_app.py`, `src/media_hygiene/review/home_tags_api.py`, `src/media_hygiene/services/home_tags.py`, `src/media_hygiene/services/tags.py`, `src/media_hygiene/review/templates/home_run.js.j2`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`

## Why

Leftovers of 0343, decided by the maintainer (inbox, 2026-10-27).

## What

1. Survey the other long read-only steps (`people` face scan, `meaning`, `inventory`, phone
   import): duration measured or estimated on the demo tree, and for each, whether it moves into
   the page as `tags` did (figures, run, progress, Stop). File one TODO per step worth it.
2. The last photo's words in the progress of `tags` (a hook in `TaggingStore`).

Kept as they are: the console prints nothing for a page run; *Describe for 1 h* stays a constant.
