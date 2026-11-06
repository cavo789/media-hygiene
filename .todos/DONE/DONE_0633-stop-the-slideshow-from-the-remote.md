# 0633 — The phone's remote has a Stop button for the slideshow

- **Priority**: Medium
- **Batch**: phone
- **Depends**: —
- **Files**: `src/media_hygiene/review/album_show.py`, `documentation/en/commands/slideshow.md`, `documentation/fr/commands/slideshow.md`

## Problem

Follows 0615 (commit 1a17e45b). The remote has no way to stop a show: its help says *choose another
show here; the PC alone stops the slideshow*.

## Decided (2026-11-06, maintainer, review of the iterate of 2026-11-06)

Add a Stop button to the remote; the help's sentence changes with it. Off the PC everything stays
read-only: Stop ends the show, it touches no photo and no setting.

## Acceptance

- [ ] Stop on the remote ends the show on the TV; the TV says so, and the remote offers a new show
- [ ] It works from any paired phone; the phone gets no other write
- [ ] The help of the phone (at most 120 words, no command) and both languages of the docs updated
- [ ] `docs_screenshots` flagged as stale
