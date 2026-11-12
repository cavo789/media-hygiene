# 0733 — What 0373 left: Videos get a thumbnail: a frame decoded once, kept in the cache

- **Priority**: Medium
- **Batch**: videos
- **Depends**: —
- **Files**: `.todos/DONE/0373-video-thumbnails-from-a-keyframe.md`, `src/media_hygiene/scan/keyframes.py`, `src/media_hygiene/scan/video_still.py`, `src/media_hygiene/report/thumbnails.py`, `src/media_hygiene/share/album_view.py`, `src/media_hygiene/slideshow/pictures.py`, `tests/integration/test_album_phone.py`

Split from section 0373 of PARTIAL 0718 (`.todos/PARTIAL/PARTIAL_0718-code-left-in-partial-todos.md`), as decided by the maintainer in the review of 2026-11-12 (one TODO per remaining section). Source TODO: `.todos/DONE/0373-video-thumbnails-from-a-keyframe.md`.

## Left (as listed in 0718; the source TODO has the full wording)

- The album page (`share/album_view.py`) and the slideshow's phone grid (`slideshow/pictures.py`)
- An HEVC `.MOV` in the large view: Edge plays it only with the HEVC extension installed; not

## How to proceed

- Check each item against the code first: some may be done already and only unticked (then say so and close them).
- File follow-ups for what is really left; every figure says *measured* or *estimated*; a new limit: say whether it should be a setting.
- Documentation EN + FR and French strings when something user-facing changes.
