# 0799 — Person large view asks tag

- **Priority**: Low
- **Batch**: people
- **Depends**: —
- **Files**: TBD

Follows PARTIAL 0723 (`.todos/PARTIAL/PARTIAL_0723-browser-kept-pictures-for-the-rest.md`); decided by the maintainer in the review of 2026-11-13 (`.claude/plans/feedback-2026-11-13-iterate.md`).

On the person page, the picture tag of the large view is asked when the large view opens (not for every tile at page load). Shared large view (`pick_*`, skill `photo-picking-pages`).

## Status — DONE (2026-11-27)

The large view asks `GET /api/photo-tag/<n>` once when a photo opens (`people/pictures.photo_tag`, one stat), then shows `/photo/<n>.jpg?v=<tag>`; `jpeg_response` keeps it for good when the tag matches. Test: `test_people_page.py`.
