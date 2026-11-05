# 0617 — Library page: the `/library` address, `/search` redirects

- **Priority**: Low
- **Batch**: search
- **Depends**: 0486 (DONE)
- **Files**: `src/media_hygiene/search/`, `src/media_hygiene/review/`, `documentation/en/`, `documentation/fr/`

## Why

Review of 0486: the verb became `library`, the page stays at `/search`; the maintainer wants the address renamed too.

## What

Serve the page at `/library`; `/search` (and its sub-paths, query string kept) answers a redirect, so saved favourites, bookmarks and links keep working. The `search` action id stays.

## Done when

Old and new addresses both open the page (test); docs in both languages name `/library`.
