# 0794 — Profile people page cold open

- **Priority**: Medium
- **Batch**: page-speed
- **Depends**: —
- **Files**: `src/media_hygiene/faces/`, `src/media_hygiene/review/`

Follows DONE 0722 and DONE 0756; decided by the maintainer in the review of 2026-11-13 (`.claude/plans/feedback-2026-11-13-iterate.md`).

The people page cold open at 100k synthetic files spends about 9 s outside the grouping (estimated in 0756 from its timings). Measure first with `py-spy record` (method: `measure-before-ranking` skill, synthetic data, light machine load), list where the time goes, measured. No product change until the figures are in this TODO.

## Status — DONE (2026-11-13)

Measured: pages bench, 100,000 synthetic files (50,347 faces, 60 people), devcontainer, `nice -n 19`, `PYTHON_CPU_COUNT=4`. Bench fix first: the synthetic library now records a turn guess per photo with faces (since 0803 the page answered 409, "faces still to be found").

- People page cold open: **11.8 s** plain run; 15.1 s under `py-spy record -r 50` (overhead ~27 %). Warm: 0.2 ms (kept state, 0804). `people groups` after it: 68 ms.
- Where the time goes (py-spy, 14.9 s sampled inside `people_here._built`):
  - grouping `faces/cluster.face_labels` 12.3 s (82 %), of which `neighbours` 11.0 s: matrix product 4.4 s, threshold compare 2.0 s, `_floor` partition 2.0 s, `flatnonzero` 1.2 s, `_closest` 0.7 s; Chinese whispers 1.0 s;
  - `PeopleStep.plan` 1.8 s (12 %): `people_photos` 1.0 s, per-photo `scanned`/`guessed` SQL 0.7 s;
  - the rest (page build, labels) ~0.8 s.
- The 0756 estimate ("about 9 s outside the grouping") does not hold on this bench: outside the grouping is ~2.6 s profiled (~2 s plain).

Follow-ups: 0814 (keep face links in the index: only new faces compared; High), 0815 (plan in one query per table; Low).
