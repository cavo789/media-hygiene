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

- [x] Picked, the page reloads in that language; other open pages follow at their next load
  (`install()` on save via `SettingGroup.applied`; Jinja translates at render time
  (`install_gettext_callables`); the home and library pages are drawn once per language,
  `i18n/live.PerLocale`).
- [x] Console messages of the running server follow too (`install()` is process-wide); the
  page says which stay: a slideshow, the phone pages and the review pages already drawn keep
  theirs until mh starts again.
