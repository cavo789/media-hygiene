# 0640 — Sort trial offered first, by the sort confirmation and on the page

- **Priority**: Medium
- **Batch**: sort
- **Depends**: —
- **Files**: `src/media_hygiene/cli/cmd_sort.py`, `src/media_hygiene/services/sort_trial.py`

## Problem

Rest of 0526 (commit 151f8cfb, PARTIAL). `sort --trial` exists in the console only: no page
button, no view of the photos in their new folders (rule *Seeing first*), and the sort's
confirmation does not offer it.

## Decided (2026-11-06, maintainer, review of the iterate of 2026-11-06 (2))

Keep the latest month as the default sample. The sort's confirmation offers the trial first, and
the page gets *Try on one month* with the moved photos shown in their new folders.

## Acceptance

- [ ] The confirmation of a first sort offers the trial first
- [ ] The page: *Try on one month*, then the photos shown where they went, *Undo* and *Sort the rest*
- [ ] Both languages of the docs updated; `docs_screenshots` flagged as stale
