# 0635 — Named faces: the content id read from the index, the file only when it has no digest

- **Priority**: Medium
- **Batch**: people
- **Depends**: —
- **Files**: `src/media_hygiene/services/face_refs.py`

## Problem

Found while reviewing 0570 (commits 7112f5ff, 3c5ffe54): `current_id` reads the whole file even
when the index already holds its digest. The one-time line counts only the photos without a
digest, but more photos than that are read: the first audit after the upgrade is slower than said.

## Acceptance

- [ ] A photo whose (path, size, mtime) row has a digest is not read again (test)
- [ ] The line "N named photos read once" counts exactly the photos read
- [ ] Measured: the first audit after the upgrade, before → after (synthetic, *measured*)
