# 0794 — Profile people page cold open

- **Priority**: Medium
- **Batch**: page-speed
- **Depends**: —
- **Files**: `src/media_hygiene/faces/`, `src/media_hygiene/review/`

Follows DONE 0722 and DONE 0756; decided by the maintainer in the review of 2026-11-13 (`.claude/plans/feedback-2026-11-13-iterate.md`).

The people page cold open at 100k synthetic files spends about 9 s outside the grouping (estimated in 0756 from its timings). Measure first with `py-spy record` (method: `measure-before-ranking` skill, synthetic data, light machine load), list where the time goes, measured. No product change until the figures are in this TODO.
