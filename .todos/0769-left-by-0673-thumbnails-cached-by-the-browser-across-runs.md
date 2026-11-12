# 0769 — What 0673 left: Thumbnails kept by the browser across runs: content-named URLs, never asked again

- **Priority**: Medium
- **Batch**: page-speed
- **Depends**: —
- **Files**: `.todos/DONE/0673-thumbnails-cached-by-the-browser-across-runs.md`, `src/media_hygiene/report/preview_cache.py`, `src/media_hygiene/search/pictures.py`, `src/media_hygiene/search/hits.py`, `src/media_hygiene/places/photos.py`, `src/media_hygiene/person/pictures.py`, `src/media_hygiene/review/respond.py`

Split from section 0673 of PARTIAL 0718 (`.todos/PARTIAL/PARTIAL_0718-code-left-in-partial-todos.md`), as decided by the maintainer in the review of 2026-11-12 (one TODO per remaining section). Source TODO: `.todos/DONE/0673-thumbnails-cached-by-the-browser-across-runs.md`.

## Left (as listed in 0718; the source TODO has the full wording)

- The other tile servers keep the per-run `ETag`: person, people, places, reviews, events
- Accepted limits (reviewer): a file replaced with the same size and mtime keeps its tag
- One test per invalidation event above
- Requests and bytes for a 200-tile page, second visit, before / after, in the PR

## How to proceed

- Check each item against the code first: some may be done already and only unticked (then say so and close them).
- File follow-ups for what is really left; every figure says *measured* or *estimated*; a new limit: say whether it should be a setting.
- Documentation EN + FR and French strings when something user-facing changes.
