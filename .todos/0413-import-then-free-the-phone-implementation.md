# 0413 — Import then free the phone in one go: the implementation

- **Priority**: Medium
- **Batch**: phone
- **Depends**: 0336
- **Needs maintainer**: the result of step 19r of `mh-measure.ps1` (CopyHere vs MoveHere, 20 synthetic files), run with `.\mh-measure.ps1 -Only 19 -Count 1`
- **Files**: see the design note of 0337 (`.claude/plans/0337-import-then-free.md`, private)

## Context

0337 (commit 03fc792, PARTIAL) wrote the design note only. Decided by the maintainer in the
review of 2026-10-27:

- "move, then compare" is accepted: MoveHere stays (no MTP delete without a dialog, 0248; no
  Add-Type, Avast); the moved copy is compared with the import's SHA-256, one that differs is
  kept in the quarantine;
- a file imported in the same session skips the proof copy only when the phone shows the same
  size and date again and the library copy is hashed again, equal, and passes the image check;
- one `keep_folders` list for every phone (a setting), not one per phone;
- `mh phone` ends on the free page.

## Steps

The four implementation parts listed in the design note, each with the proof tests it lists.

## Acceptance

- After an import, freeing reads each file once instead of twice (estimated 6 → 3 min for
  4.2 GB at 24 MB/s; measured by step 19r).
- No file leaves the phone without a verified copy on the PC.
