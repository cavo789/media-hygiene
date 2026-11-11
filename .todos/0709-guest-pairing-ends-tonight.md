# 0709 — A guest pairing ends the same evening

- **Priority**: Medium
- **Batch**: lan
- **Depends**: —
- **Files**: `src/media_hygiene/share/album_guest_door.py`, `src/media_hygiene/review/`

Filed 2026-11-11 by the review of `feedback-2026-11-11-iterate.md` (0684 (bb3f90af)), decided by the maintainer.

## Context

0684 added guest devices (chosen albums only); a guest pairing lasts until forgotten, like a family phone. Decided: it ends the same evening (a relative's TV does not keep access).

## Acceptance

- [ ] A guest token expires at the end of the day (constant, local time) — test with a fixed clock
- [ ] The card says until when; an expired guest gets the pairing page
