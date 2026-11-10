# 0677 — First click after the server starts is as fast as the next ones

- **Priority**: Low
- **Batch**: page-speed
- **Depends**: —
- **Files**: `src/media_hygiene/review/home_app.py`, `src/media_hygiene/services/home.py`, `src/media_hygiene/services/search_app.py`, `src/media_hygiene/search/fts.py`

Filed by the UX / speed / security review of 2026-11-10 (asked by the maintainer; analysis only, no code changed).

## Context

*Measured* (devcontainer, demo tree of 28 files, `curl`, 2026-11-10) — first call after the
server started, then the same call again:

| Call | First | Next |
|---|---|---|
| `GET /library` | 1.058 s | 0.5 ms |
| `GET /api/state` | 0.313 s | 6–7 ms |
| `POST /api/search` | 0.259 s | 2 ms |
| `GET /thumb/52.jpg` (a video frame) | 0.216 s | 1 ms |

With 28 files, the first-call cost is imports and set-up, not data. On a real library the
first search also builds the full-text table (about 650 ms for 100,000 files, measured in
0353). The home page itself is ready under a second (0442).

## Proposal

- Once the server listens (never before: the page must show first), a background task at
  low priority runs what the first clicks will need: import the library page's modules and
  render its template once, open the index and build the full-text table, start the worker
  pool (`warm_pool` exists for the audit).
- Cancelled without a trace when the server stops; nothing written; skipped on a phone-only
  session is not needed (same server).
- Measure on the maintainer's PC only if the devcontainer gain does not show there.

## Acceptance

- [ ] First `GET /library` and first search after a start, before / after (same method)
- [ ] The time for the home page to answer its first request does not grow

## Where the user gains

First opening of the library after `mh` starts: about 1.3 s of waits (page + first search,
measured on the demo) → as the next ones (ms).
