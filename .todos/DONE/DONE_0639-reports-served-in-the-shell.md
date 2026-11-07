# 0639 — Reports served by the home server inside the home page's frame

- **Priority**: Low
- **Batch**: page-shell
- **Depends**: —
- **Files**: `src/media_hygiene/review/report_files.py`, `src/media_hygiene/report/templates/`

## Problem

Rest of 0498 (commit 47878543, PARTIAL). A report served over http gets the home page's look
and its way back through a client script; the server serves the file as it is: no
server-rendered shell, no current space highlighted.

## Decided (2026-11-06, maintainer, review of the iterate of 2026-11-06 (2))

Serve `/reports/<run>/…` inside the real shell of the home page. A report opened from the disk
stays readable alone.

## Acceptance

- [ ] Served: the shell's sidebar with the Reports space highlighted (test on the rendered page)
- [ ] Opened from disk: unchanged, nothing of the home page
