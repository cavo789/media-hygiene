# 0634 — The audit stores a digest for every video, so Tag and the place never wait on one

- **Priority**: Medium
- **Batch**: index
- **Depends**: —
- **Files**: `src/media_hygiene/scan/exact.py`, `src/media_hygiene/search/tag_cap.py`

## Problem

Follows 0571 (commit e5500be2). Above 200 picked files without a digest, Tag and the place given
by hand refuse and say "run an audit first". An audit only probes a video, so a video of unique
size never gets a digest: the refusal can last for ever.

## Decided (2026-11-06, maintainer, review of the iterate of 2026-11-06 (2))

Store a digest for videos too, so "run an audit first" always works.

## Acceptance

- [ ] After an audit, every video has a digest in the index; measured cost on a large video folder (*measured*, how)
- [ ] Invalidation: rename, move, in-place write, copy keeping the mtime, `touch` (one test each)
- [ ] `cache-invalidation-reviewer` run on the diff
