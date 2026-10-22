# 0302 — browse: the heaviest files of the whole library

- **Priority**: Medium
- **Batch**: review-ui
- **Depends**: 0301
- **Files**: `src/media_hygiene/search/folders.py`, `src/media_hygiene/search/heaviest.py` (new), `src/media_hygiene/search/statements.py`, `src/media_hygiene/search/app.py`, `src/media_hygiene/search/templates/browse.html.j2`, `src/media_hygiene/search/templates/browse.js.j2`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/commands/browse.md`, `documentation/fr/commands/browse.md`, `tests/integration/tags/test_browse_page.py`
- **Needs maintainer**: the place of the view (an entry at the top of the tree, or a mode of the search page)

## Why

On 2026-10-22 the maintainer asked "which videos are really huge, and can I convert them?" Going
through folders one by one (0301) cannot answer that. The index already holds what is needed:
`size` for every file, and for videos `duration`, `bit_rate`, `codec`, `width`, `height`
(`MediaMetadata`, from the audit's `ffprobe`). Today only `inventory.xlsx` shows all of it.

Measured on the maintainer's index (2026-10-17, read-only, `.claude/plans/proposals-2026-10-17-competitors.md`):
1,531 videos = 98.3 GB, 40.8 % of the 240.9 GB; 325 MJPEG clips = 24.4 GB at 12.7 Mb/s on
average. A handful of files hold most of the space, so a list of the heaviest is the shortest way
to them.

## What

- An entry **Heaviest files** at the top of the tree (recommended: no new page or route to learn;
  the search page is the alternative). It lists the N heaviest files of every mounted folder in
  the grid browse already has, with the **Show** filter of 0301 (videos by default here).
- Orders: **size** (default) and, for videos, **bit rate** (bytes per second of film). Bit rate
  finds the clips that are badly compressed for their length, the best candidates for 0303.
  Sorting by size alone puts a long, well-compressed film first.
- Each video tile shows its folder (host path, so the user knows where it lives), size, duration,
  codec and resolution: `2.1 GB · 12 min · mjpeg · 1280×720`.
- N: 200 at first. Should it be a setting? Probably not: a "show more" button is enough (to
  decide during implementation).
- Set aside, viewer, Ctrl+A: as in a folder. A header line gives the total of what is listed
  ("200 files, 61.4 GB, 25 % of your library").
- SQL: `ORDER BY size DESC LIMIT ?` on `files`, with the metadata JSON read only for the rows
  returned. `search/app.py` is at 195/200 lines (measured, `near_limit.sh`): the route goes in a
  new module (`heaviest.py`).

## Tests

- Files from two roots, ordered by size; ties by path; the limit; `kind=videos`; bit-rate order
  with a video whose `bit_rate` is unknown (last, never a crash); a file outside the mounted
  roots is never listed.

## Docs

`commands/browse.md` in both languages; in the clean/sort guides, a pointer "find what takes
the space". The page changes: `docs_screenshots` should run afterwards (not unasked).
