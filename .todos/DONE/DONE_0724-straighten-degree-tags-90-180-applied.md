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

## Decided (2026-11-13)

The degree tags `90`/`180` are read when the preview is made: only the previews of those photos are rebuilt, no global preview `_VERSION` bump (choice by the maintainer, review of `.claude/plans/feedback-2026-11-13-iterate.md`).

## Status — DONE (2026-11-13)

- `scan/degree_tags.py`: `90`/`180` applied in `upright_picture` (as codes 6/3), and in
  `people/crops.upright_size` (face boxes' frame). `report/preview_cache.preview_key` reads
  the tag when a preview is made: a degree-tagged photo's preview gets a new name
  (`_DEGREES_VERSION`), every other preview keeps its name (test rebuilds the old name).
- Face rows: the first `people` run after 0725 re-analyses whole the photos tagged in degrees
  (its turn-only pass reads each header); other photos' faces untouched.
- Visual facts (dHash/pHash) left as computed (deviation, by the decision: only previews):
  identical copies share the tag, so their hashes stay comparable.
- Invalidation tests (`tests/unit/test_degree_tags.py`): tag written later by an atomic save
  with the mtime put back, copy keeping its mtime, file gone; in-place write/touch/rename
  give a new key through size/mtime/path as before.
- Cost, measured (1,000 synthetic JPEGs, devcontainer, warm): 0.043 ms per header read →
  ~4.3 s per 100,000 previews asked (estimated, warm cache; paid only when a preview is
  asked, not per index row).
