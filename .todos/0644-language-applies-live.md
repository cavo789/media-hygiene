# 0644 — The language picked on a page applies at once

- **Priority**: Low
- **Batch**: settings-on-pages
- **Depends**: —
- **Files**: `src/media_hygiene/i18n/`, `src/media_hygiene/review/page_settings.py`

## Problem

Follows 0609 (commit d1bf8ed2). The language picker writes `[general] locale`, applied at the
next start only.

## Decided (2026-11-06, maintainer, review of the iterate of 2026-11-06 (2))

Applied live: the page reloads in the new language, the server's catalog switched.

## Acceptance

- [ ] Picked, the page reloads in that language; other open pages follow at their next load
- [ ] Console messages of the running server follow too, or the page says which stay
