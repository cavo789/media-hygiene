# 0418 — shrink: albums, decisions and plans follow a video renamed `.avi` → `.mp4`

- **Priority**: Low
- **Batch**: videos
- **Depends**: —
- **Files**: `src/media_hygiene/shrink/`, `src/media_hygiene/share/album_follow.py`, `src/media_hygiene/people/followed.py`, `src/media_hygiene/report/decisions.py`, `src/media_hygiene/services/sort_report.py`

## Why

Leftover of 0303, decided by the maintainer (inbox, 2026-10-27). When `shrink` writes the lighter
`.mp4` of an `.avi`, an album entry, a `decisions.json` choice or a classify `plan.json` row naming
the original then names a file in the quarantine (each feature says "missing"). 0382 rewrites
these files after `sort` / `undo`: reuse that rewrite for `shrink` (and for its `undo`).
Rarely relevant (estimated: few old MJPEG clips are in albums).

## Tests

A video in an album and in `decisions.json`, shrunk: both name the `.mp4`; `undo`: both name the
original again.

## Status

DONE (2026-10-29). `services/shrink_links.renamed` lists the videos a run renamed from its
journal (`SHRUNK` entries: `keeper` → `path`, reversed for `undo`); `shrink --apply` and `undo`
hand them to `follow_links` (0382): face lists, `albums.json`, `decisions.json`, `--try`
choices are rewritten and read back. Test: `tests/integration/test_shrink_links.py`.
Not done: a classify `plan.json` row is not rewritten (sort's rewrite does not cover it either;
a video renamed between classify and sort is reported missing by `sort`, as before).
