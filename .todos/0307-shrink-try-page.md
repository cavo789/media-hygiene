# 0307 — `shrink --try`: compare before and after in the browser, then lighten from the page

- **Priority**: High
- **Batch**: shrink
- **Depends**: —
- **Files**: `src/media_hygiene/cli/cmd_shrink.py`, `src/media_hygiene/services/shrink.py`, `src/media_hygiene/shrink/drafts.py` (new), `src/media_hygiene/review/shrink_app.py` (new), `src/media_hygiene/review/shrink_views.py` (new), `src/media_hygiene/review/templates/shrink.html.j2` (new), `src/media_hygiene/review/videos.py`, `src/media_hygiene/review/apply_api.py`, `src/media_hygiene/actions/shrink.py`, `src/media_hygiene/config/shrink_settings.py`, `src/media_hygiene/config/templates/config.toml.j2`, `src/media_hygiene/cli/menu_catalog_clean_more.py`, `documentation/en/commands/shrink.md`, `documentation/fr/commands/shrink.md`, `tests/integration/test_shrink_try.py` (new)

## Why

Today `shrink` is CLI-only: `mh shrink` lists, `mh shrink --apply` re-encodes for real, and the
home page's button only runs the list in the console. Nobody can see a lightened video before its
original goes to the quarantine. The maintainer's only look so far was `mh-measure.ps1` step 34
(a test tool, not the product). Decided by the maintainer (2026-10-23): a web page, a draft of
`try_count` videos (10 by default), and an "Lighten this one" button.

## What

1. `mh shrink --try` (and the home page's action, which becomes a `Kind.PAGE`) opens a page
   served like `review` (loopback `Host`, JSON-only `POST`). It takes the first `[shrink]
   try_count` candidates (default **10**, `ge=1`), in the list's order (largest gain first), or
   those below `--folder`.
2. The drafts are encoded **one at a time in the background**, with the same `Recipe` as
   `--apply`: the page shows the first one as soon as it is ready, then the next ones as they land.
   Estimated, from the 2026-10-23 measurements (about 8 s of encoding per minute of film, 16
   threads): the largest clips (215 s) take about 30 s each, so 10 of them about 5 min. Hence one
   at a time, never the whole batch first.
3. Per video: the lightened MP4 played in the page (`review/videos.py`, `Range`), sizes, gain
   in %, encoding time. **Before**: the originals (MJPEG + PCM in `.MOV`) play in no browser (to
   check per codec, but true for the measured Panasonic clips). So the "before" side shows frames
   extracted at the same instants as the "after" side (10 %, 50 %, 90 %), side by side, 100 %
   zoom, one key to swap A/B. ← / → move between videos.
4. **Lighten this one** / **Lighten all shown**: the page records the choice
   (`shrink-decisions.json` in `/cache/shrink-try/`, read back from disk and shown), then ends with
   the home page's step code (`apply_api.py`, as `clean --decisions`). `mh` runs
   `shrink --apply --decisions`, its usual question included. **The draft is reused, never encoded
   twice**: when the original still has the size and mtime it had when encoded, the draft is
   proven again (`shrink.check`) and moved beside it with `move_no_replace` (another volume:
   proven copy), then the run goes on as today (quarantine, rename, journal). An original changed
   since is encoded again. Estimated gain: the encoding time of each video chosen (about 30 s per
   large clip).

## The drafts are always removed

They are never written next to the photos, nor in a folder Windows sees: only in
`/cache/shrink-try/<run>/` (the `media-hygiene-cache` volume).

- Removed when the page closes, in a `finally` inside the command: normal end, Ctrl+C, error.
  `docker stop` sends SIGTERM, which Python does not turn into an exception by default (to check
  against `services/interrupt.StopRequest`): handle it like Ctrl+C, else the sweep below catches
  it. The quiet end (`teardown`, armed only once the command has returned) comes after the
  removal.
- Left by a crash (`docker kill`, PC off): any `shrink` (list, `--try`, `--apply`) first empties
  `/cache/shrink-try/` and says so in one line ("previous draft removed: N MB"). Only when no
  other `shrink --try` runs (a lock file with the PID in that folder).
- Without a `/cache` mount (a bare `docker run`): `--try` refuses with the line to add, never a
  fallback to `/tmp` inside a container whose disk usage nobody watches.
- Disk space: a draft weighs about 29 % of its original (measured, 2026-10-23), so the 10
  heaviest of C:\Photos take about 1.7 GB (estimated: 10 × 574.8 MB × 29 %). Before each
  encoding, check the free space of `/cache` (at least twice the estimated size) and stop the
  drafts there with a line.
- One test per case: page closed, Ctrl+C, error during an encoding, folder left by a crashed
  run, two `--try` at once, no `/cache`.

## Paths

A decision is stored by path (container path, size, mtime). Moved or renamed between the page and
`--apply` (Explorer, `sort`, `undo`): no match, so the video is skipped with a line, never
encoded from a stale path. Test it.

## Settings

`[shrink] try_count` (default 10), in `config.toml.j2` with its comment and in both
documentation pages. The disk-space margin (twice the estimate) stays a constant unless the
review asks for a setting.

## Docs

`commands/shrink.md` in both languages: `--try`, the page, the drafts removed. Captures stale:
`docs_screenshots` to run (not unasked).
