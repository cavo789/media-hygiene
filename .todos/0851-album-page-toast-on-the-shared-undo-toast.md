# 0851 — The albums page's toast moves onto the shared undo toast

- **Priority**: Low
- **Batch**: page-shell
- **Depends**: none
- **Files**: the albums page templates, `undo_toast` (shared), `tests/unit/test_undo_toast.py`

## Why (review of feedback-2026-11-27-iterate, maintainer's choice)

0811 (commit 5df8e265) left the albums page with its own local toast and Undo, while places and the reviews use the shared one. Two versions drift apart.

## Do

- The album deleted (and every other album action with an Undo) uses the shared `undo_toast`; the local toast is removed.
- Behaviour kept: restore from `albums-deleted.json`, read back and shown.
