# 0485 — Home page random photos replace the copies preview

- **Priority**: Low
- **Batch**: home
- **Depends**: 0483
- **Files**: new `src/media_hygiene/cli/home_samples.py`, `src/media_hygiene/cli/home_findings.py`, `src/media_hygiene/review/home_parts.py`, `src/media_hygiene/review/templates/home_draw.js.j2`

"Copies, in preview" leads to the reports, as "Recent reports" already does. The maintainer
likes the thumbnails: keep the idea as "Random photos".

- About ten readable photos drawn from the index at each page load (view only, not picking
  tiles); previews from the existing preview cache.
- A click opens the Library (search page) on that photo's folder (event).
- Remove the copies preview part.
- Tests: empty index (block hidden), fewer than ten photos, a file gone from disk skipped.
- Count of ten: a named constant (see few-settings rule), not a setting.
