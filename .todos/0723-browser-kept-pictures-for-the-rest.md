# 0723 — Browser-kept pictures for the remaining tile pages (file version from the index)

- **Priority**: Medium
- **Batch**: page-speed
- **Depends**: —
- **Files**: `src/media_hygiene/slideshow/pictures.py`, `src/media_hygiene/review/versioned.py`, `src/media_hygiene/review/events_views.py`, `src/media_hygiene/people/templates/people_viewer.js.j2`, `src/media_hygiene/share/album_view.py`

Follows PARTIAL 0701 (`.todos/PARTIAL/PARTIAL_0701-thumbnails-cached-on-every-tile-page.md`, commit 479e9e53): the review pages, places and person keep their pictures in the browser through `…?v=<tag>` (`review/versioned.py`). Left: slideshow, TV, albums (`thumb_path` and `tv_path` take a key only), the library's Events tab (plan rows have no size/mtime), the people page's large view (built in JS from `PHOTO + key`), the storyteller thumbnails (`slideshow_story.js`) and the home page samples.

Decided by the maintainer in the review of 2026-11-12.

## What

- Give each of these the same `?v=<tag>` rule, the file's version (size, mtime, preview version) **read from the index**, not stat-ed per tile.
- One test per invalidation event, as 0701 did: edit in place, same time other size, atomic save, touch, rename/move, preview version bump, file gone.

## Acceptance

- [ ] Each listed page answers `immutable` for the current version and the run's rule otherwise (tests).
- [ ] Requests and bytes on a second visit, before / after (measured).
- [ ] A file moved by `sort`/`undo`: the tag follows (test).
