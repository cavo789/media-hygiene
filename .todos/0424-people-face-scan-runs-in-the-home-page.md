# 0424 — The face scan of `people` runs in the home page, as `tags` does

- **Priority**: Low
- **Batch**: home
- **Depends**: —
- **Files**: `src/media_hygiene/cli/people_flow.py`, `src/media_hygiene/services/home_tags.py`, `src/media_hygiene/review/home_app.py`, `src/media_hygiene/review/templates/home_run.js.j2`, `documentation/en/commands/people.md`, `documentation/fr/commands/people.md`

## Why

Survey of 0421 (2026-10-27). The face scan is the longest read-only step after `tags`: it
writes the cache only, the photos stay read-only. On `C:\Photos` (52,094 media, 27,159 faces,
index of 2026-10-17) a first scan is *estimated* at hours on the processor (≈0.2–0.5 s per photo,
from the detector's usual CPU cost; to measure with `mh-measure.ps1`), during which the console
of `mh` is minimised behind the home page.

## What

1. The same shape as `tags` in the page (0343): figures first (photos left to scan, estimated
   time), *Scan now* / *For 1 h* / *Not now*, progress with the last photo's count of faces,
   Stop after the photo in flight; each photo's faces committed at once (a stop keeps them).
2. Reuse `HomeTags`' runner (a second `TagsRunner`-like pair of halves) rather than a copy.
3. Tests: prepare → figures, describe → progress, Stop; docs en + fr.

## Acceptance

- From the home page, the faces scanned with a progress and a Stop; the people page shows them.
