# 0308 — A video lightened by `shrink` carries its mark: never proposed again, even moved

- **Priority**: Medium
- **Batch**: shrink
- **Depends**: —
- **Files**: `src/media_hygiene/shrink/encode.py`, `src/media_hygiene/scan/video_meta.py`, `src/media_hygiene/shrink/candidates.py`, `src/media_hygiene/actions/not_worth.py`, `tests/integration/test_shrink.py`, `tests/unit/test_shrink_candidates.py`

## Why

Today three things keep `shrink` from proposing a video it wrote itself:

1. its codec, H.264, is not in `[shrink] codecs`;
2. at CRF 23 it spends far less than `bits_per_pixel` (0.5): about 0.22 bit per pixel
   (estimated: the `estimate` calibration on the two clips measured on 2026-10-23);
3. the journal's `shrunk` lines (`not_worth.py`), keyed by **path, size and mtime**.

The third one is lost when the file moves: renamed or moved in Explorer, moved by `sort`, or when
the journals are gone. Only 1 and 2 are left then. They fail together when a user lowers
`same_crf` (CRF 18 measured at about 0.55 bit per pixel on 2026-10-23, above 0.5) or raises
`bits_per_pixel`'s strictness. The video would then be encoded a second time: quality lost for
little gain.

## What

- `encode.py`: write a tag into the MP4 (`-metadata comment=…` or a dedicated key, to check which
  one survives `use_metadata_tags` and Windows' Properties without hiding the camera's own
  comment), e.g. `media-hygiene shrink crf=23`.
- The audit's video probe (`video_meta`) reads it into `MediaMetadata` (schema version bump, the
  index upgrade path in `index/schema`).
- `candidates.py`: a video carrying the mark is never a candidate, whatever its path, codec or
  rate. The journal check stays (it also covers the not-worth marks, which have no file to tag).
- Tests: a lightened video renamed, moved to another folder, journals deleted, `same_crf = 18`:
  never listed again. One per event (`.claude/rules/workflow.md`).
