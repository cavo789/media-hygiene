# 0162 — A failed file says why in plain words, never `[Errno 1] … '/data/c/…'`

- **Priority**: Medium — a failing `undo` printed 4,000 lines of raw Python errors with the container's paths; the user asked whether the paths were wrong
- **Batch**: guidance
- **Depends**: —
- **Files**: `src/media_hygiene/actions/undo.py`, `src/media_hygiene/actions/xmp_write.py`, `src/media_hygiene/actions/parallel.py`, `src/media_hygiene/actions/sort.py`, `src/media_hygiene/actions/sort_cleanup.py`, `src/media_hygiene/actions/album_links.py`, `src/media_hygiene/actions/outcome.py`

## Context

Seen by the maintainer on 2026-10-14 (`mh-measure.ps1 -Only 7`, an `undo` of a sort failing on
Docker Desktop, cause fixed in 0138):

```
❌ C:\Users\…\data\copies\002000-S3502056.JPG: [Errno 1] Operation not permitted:
'/data/c/measure/copies/002000-S3502056.JPG'
```

The Windows path is right, then `str(exc)` repeats the errno and the container path
(`/data/c/…`), which means nothing to a user ("is that path normal under PowerShell?").
`UndoExecutor.run` (`undo.py:96`) and `xmp_write.py:101` store `str(exc)`; `parallel.py`,
`sort.py`, `sort_cleanup.py`, `album_links.py` use `exc.strerror or str(exc)` (better, but
untranslated and the fallback is still raw). Thousands of identical failures are printed one
per line.

## What to do

1. One helper (e.g. `actions/outcome.why(exc)`) turning an `OSError` into a short translated
   reason by errno: `EPERM`/`EACCES` "not allowed (owner or permissions)", `ENOSPC` "the disk is
   full", `EEXIST` "something is already there", `ENOENT` "no longer there", `EROFS` "read-only
   mount", else `exc.strerror`; never the path (the line already shows the Windows one), never
   `[Errno n]`. Our own `OSError(_("…"))` messages pass through unchanged.
2. Use it at every `Incident(…, str(exc))` / `exc.strerror or str(exc)` above.
3. When more than ~20 files fail for the same reason, show the first few, then one line
   "… and 3,980 more: <reason>" (the full list stays in the report/journal). Say in the report
   whether that count should be a setting.
4. Translations (fr); the raw text stays in the debug log (`--verbosity debug`).

## Acceptance

- Unit tests: `why()` per errno, no `/data/` and no `[Errno` in the result; an `undo` with 50
  identical failures prints a handful of lines and the summary.
- Console output changes: say that `docs_screenshots` should run.
