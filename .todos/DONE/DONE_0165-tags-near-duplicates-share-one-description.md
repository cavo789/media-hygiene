# 0165 — `tags`: a group of near duplicates is described once, its kept version answering for its copies

- **Priority**: Low
- **Batch**: tags
- **Depends**: —
- **Files**: `src/media_hygiene/tags/selection.py`, `src/media_hygiene/services/tag_describe.py`, `src/media_hygiene/plan/near.py`, `src/media_hygiene/review/near_file.py`, `tests/integration/tags/`, `documentation/en/reference-tags.md`, `documentation/fr/reference-tags.md`

## Context

Follows 0083 (closed DONE on 2026-10-15): videos and `classify` reusing the `tags` answers are
delivered; near-duplicate groups (`plan/near`, `near_video`) still are not. A WhatsApp copy and
its original are each sent to the vision model, while identical copies and burst series already
inherit one description (`tags/selection.vision_plan`).

Decided (inbox of 2026-10-12, 0104 §3): `tags` runs the near-duplicate search itself from the
index, instead of reading the groups of the last audit report. Measured 2026-10-12 by the
maintainer: a full `mh audit` with the cache, 52,056 media files, 10 s in all; the
`near duplicates` step alone 1.5 s on a warm audit (0131).

Decided (inbox of 2026-10-15): a group the maintainer set aside in `review --near` does **not**
share a description: each of its files is described on its own.

## What to do

1. In `tags`, find the near groups (`plan.near`, `near_video`) from the index, after the
   identical copies and the burst series are grouped.
2. The version the audit keeps answers for its copies (`vision` and `caption` tags inherited,
   as the sharpest shot does for a burst).
3. Read the `near` decisions of the last `decisions.json` (`review/near_file.py`): `leave` →
   the group is dissolved, each file is described on its own; `swap` → the copy chosen to be
   kept answers for the group; `planned` or undecided → step 2. A decisions file missing or
   unreadable: step 2 for every group (say so in the verbose log).
4. Integration test with the fake Ollama: a near pair sends one picture; the same pair with a
   `leave` decision sends two; a `swap` sends the copy kept.
5. Docs en/fr `reference-tags.md`: what is described, what inherits.

## Acceptance

- On a tree with a near-duplicate pair, `tags` sends one picture of the pair to the model;
  with a `leave` decision for that pair, two.

## Decided (2026-10-15)

- The maintainer keeps the near-duplicate search on every `tags` run, with no setting to turn it
  off (review of PR #7): ≈ 2 s is negligible on their machine.
- Only `decisions.json` and its archives are read; a file saved under a custom `--decisions`
  name is not (maintainer, review of PR #7).
