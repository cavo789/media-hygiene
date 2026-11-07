# 0647 — The language applies at once on the slideshow, phone and review pages too

- **Priority**: Low
- **Batch**: settings-on-pages
- **Depends**: —
- **Files**: `src/media_hygiene/review/page_settings.py`, `src/media_hygiene/slideshow/`

## Problem

Follows 0644 (commit cfbcd53c). Pages drawn once at start (slideshow, phone pages, review pages)
keep their language until `mh` restarts; the line after the save names them.

## Decided (2026-11-07, maintainer, review of the iterate of 2026-11-06 (3))

They follow too, by the same per-language drawing; the line of exceptions goes.

## Acceptance

- [ ] Each of these pages, reloaded after a change, is in the new language (test per page)
- [ ] The exception sentence is removed, in both languages of the docs
