# 0696 — Taking a photo out of an album: an Undo toast instead of a question

- **Priority**: Low
- **Batch**: share
- **Depends**: —
- **Files**: `src/media_hygiene/share/templates/album.js.j2`, `src/media_hygiene/share/album_edit.py`, `src/media_hygiene/share/album_store.py`, `tests/unit/test_undo_toast.py`

Decided by the maintainer on 2026-11-11, review of the iterate of 2026-11-10 (PR #77).

## Context

0663 (commit 53633d4e) replaced every native confirmation by the ask dialog; taking a photo
out of an album kept a question because no undo route existed. Decided: it is reversible, so it
gets the shared Undo toast (project rule: undoable → toast, final → dialog).

## Acceptance

- [ ] A route putting the photo back (read back from `albums.json`, shown)
- [ ] The question removed; the toast's Undo runs the route; `test_undo_toast.py` table updated
- [ ] Docs EN + FR if the albums chapter describes the question
