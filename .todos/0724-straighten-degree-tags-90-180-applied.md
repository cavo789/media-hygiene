# 0724 — Photos shown sideways: apply the degree tags 90/180 without a global preview bump

- **Priority**: Low
- **Batch**: people
- **Depends**: —
- **Files**: `src/media_hygiene/faces/straighten.py`, `src/media_hygiene/scan/visual.py`, `src/media_hygiene/index/schema.py`, `src/media_hygiene/scan/exif.py`, `tests/unit/test_straighten.py`

Follows PARTIAL 0711 (`.todos/PARTIAL/PARTIAL_0711-detect-photos-needing-rotation.md`, commit d8c3af65): the degree orientation tags `90`/`180` are not applied. Changing `upright_picture` for them shifts the cached face boxes and visual facts of those photos (12 on the maintainer's sample) and leaves their previews sideways; a global preview `_VERSION` bump would remake every preview.

Decided by the maintainer in the review of 2026-11-12.: rebuild only those photos' previews and index rows.

## What

- Apply the tags in `upright_picture`, and when a photo's tag is one of them, invalidate only its preview and its index rows (visual facts, face boxes), not the preview `_VERSION`.
- Invalidation events, one test each: tag added later in place, atomic save, touch keeping the mtime, copy keeping the mtime, rename/move by `sort`/`undo`, file gone.

## Acceptance

- [ ] A demo photo with tag 90 and one with 180 appear upright in previews and give upright face boxes.
- [ ] Other photos' previews and rows untouched (test counting rebuilds).
- [ ] Cost on a 100,000-file index stated, measured.
