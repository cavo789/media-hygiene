# 0632 — Lighten from the home page: the page says how many videos are done

- **Priority**: Medium
- **Batch**: one-interface
- **Depends**: —
- **Files**: `src/media_hygiene/services/shrink_here.py`, `src/media_hygiene/review/templates/shrink.js.j2`, `src/media_hygiene/review/step_watch.py`

## Problem

Follows 0599 (commits a4f89f3d, 828fab42). Once *Lighten* is chosen, the page follows the step
without its progress, while the docs' "Started from the home page" note says it shows how far it
is. A long encoding looks stuck.

## Decided (2026-11-06, maintainer, review of the iterate of 2026-11-06)

Add the progress to the page ("3 videos of 12"); the docs then hold true.

## Acceptance

- [ ] The figure comes from what the step wrote, read from disk, not from memory
- [ ] A closed `mh` window does not leave the page saying it is still running
- [ ] Tested with a step advancing, ending and failing
