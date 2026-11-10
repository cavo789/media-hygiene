# 0674 — Grid thumbnails made ahead (by the audit's decode or while idle), not at first display

- **Priority**: Medium
- **Batch**: page-speed
- **Depends**: —
- **Files**: `src/media_hygiene/scan/file_check.py`, `src/media_hygiene/scan/visual.py`, `src/media_hygiene/report/preview_cache.py`, `src/media_hygiene/search/thumbs.py`, `src/media_hygiene/services/audit.py`, `tests/measure/mh-measure.ps1`
- **Needs maintainer**: the first display of a never-seen folder of 200 photos on Windows + Docker Desktop, timed (a step of `mh-measure.ps1`)

Filed by the UX / speed / security review of 2026-11-10 (asked by the maintainer; analysis only, no code changed).

## Context

The 360 px grid thumbnails (`GRID_EDGE`) are rendered **when a tile is first shown**
(`search/pictures.py`), then kept in `/cache/previews`. *Measured* (devcontainer, 1 core,
file in the page cache, synthetic 12 MP JPEG of 5.4 MB, best of 5, 2026-11-10): **35.7 ms**
per thumbnail (6.4 KB), 74.4 ms for the 1600 px large view. The decode is the cost, and
reading the file comes on top: on Docker Desktop's share of a Windows disk the read of 5 MB
is likely to dominate (*not measured here* — the maintainer's step).

So the first visit of a folder of 200 photos costs about 200 × 36 ms = 7 s of CPU
(*estimated*; divided by the workers) plus 1 GB read. The audit already opens and decodes
every photo once (`VisualFacts`: dHash, pHash, sharpness).

## Proposal (measure first — skill `measure-before-ranking`)

1. Measure on the maintainer's PC the first display of 200 never-seen photos (cold) and its
   split: read vs decode.
2. Then one of, by the figures:
   - **In the audit**: the worker that decodes for `VisualFacts` also writes the 360 px
     JPEG from the same decoded picture (extra cost *estimated* a few ms: one resize + one
     encode, no second read). Disk: 6.4 KB × 50,000 photos = 320 MB (*estimated*), inside
     `[cache] previews_max_gb` — check the LRU trim does not evict them at once.
   - **While idle**: the home server renders, at low priority (1 worker, `nice`), the
     thumbnails of the folders around the one shown and of the newest import; stopped as
     soon as a request comes in.
3. Prove equivalence: a thumbnail made ahead is byte-identical to the one made on demand
   (same function, same key).

## Acceptance

- [ ] The measure of step 1 and its split in this TODO
- [ ] First display of 200 never-seen photos, before / after, measured on Windows
- [ ] The audit's time on the same tree before / after (must stay within a few %)
- [ ] Said in the report: whether "thumbnails at audit" should be a setting (a user short
      of disk space may refuse 320 MB) — proposed: a constant, on, unless the measure says no

## Where the user gains

Estimated: a never-seen page of 200 photos shows its tiles in under 1 s (200 reads of
6.4 KB) instead of several seconds of decoding — to confirm by the measure.
