# 0579 — "Your folders" in the shared sidebar of every page

- **Priority**: Medium
- **Batch**: page-shell
- **Depends**: —
- **Files**: `src/media_hygiene/review/shell.py`, `src/media_hygiene/review/templates/`, `tests/unit`

## Asked (maintainer, review of 2026-11-02)

The shared shell of 0491 (commit 3bce7836) has no "Your folders" list, which the home page's
sidebar shows. Decision: show it on every page in the frame, at the cost of one state read per
page.

## What

- The shell renders the folder list from the same source as the home page.
- The read is cheap (no walk, no hash) and a missing state shows nothing, never an error.
- Same order, same badges as the home page.

## Tests

- Every page in `SHELL_PAGES` renders the list; a page without state renders no list.
