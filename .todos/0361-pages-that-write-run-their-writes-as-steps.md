# 0361 — Pages that change photos on the home server: their writes run as steps, followed live

- **Priority**: Low
- **Batch**: home
- **Depends**: 0355, 0357
- **Files**: `src/media_hygiene/review/shrink_views.py`, `src/media_hygiene/services/shrink.py`, `src/media_hygiene/review/home_step.py`, `src/media_hygiene/actions/`, `src/media_hygiene/cli/safety.py`, `documentation/en/commands/shrink.md`, `documentation/fr/commands/shrink.md`

## Context

Phase 4 of the single server (maintainer, 2026-10-24: "be ready for the day we go all the way,
pages that write included"). `shrink` is the one page today that changes photos (re-encodes
videos in place; `PAGE_COMMANDS` minus `READ_ONLY_COMMANDS`, `cli/safety.py`).

The rule (0355): **the server never has the photos read-write**, and never Docker's socket. A
change of photos always runs in a container of its own, launched by `mh` with read-write mounts,
its write-ahead journal and its `undo`.

## What to do

1. The page asks for its write through the channel of 0355 (`.mh-step.json`, e.g.
   `shrink --apply --only <ids>`); `mh` runs it in its window; the server stays up.
2. **Progress, live**: the writing step writes its progress into a file of `/reports`
   (`.mh-step-progress.json`: done, total, current file, at most every 0.5 s); the server reads it
   and the page shows it; at the end the page reads its new state (and the journal's run).
3. Confirmation of what is final stays in the window of mh, as today (`purge`, `clean --delete`);
   a page may only ask.
4. `shrink`'s page moves to the home server (prefix, as 0356), its apply through this channel.
5. A generic test: a page step that changes files runs only through `mh` (the server's mounts are
   read-only: a write attempt from the server fails, tested).

## Acceptance

- `shrink` from the home page: the videos chosen re-encoded by a step in the window of mh, the page
  showing the progress, then the result; `undo` puts them back.

## Gain

The last page with its own container joins the single server; the same channel serves any later
page that changes photos.
