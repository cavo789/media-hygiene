# 0817 — People page built ahead after the home server starts

- **Priority**: Medium
- **Batch**: page-speed
- **Depends**: —
- **Files**: `src/media_hygiene/services/first_warm.py`, `src/media_hygiene/services/people_here.py`, `src/media_hygiene/services/kept_state.py`, `tests/unit/`, `tests/measure/pages-budget.md`

Follows 0804 (commit 59b6a913: the map, the folder tree and *Events found* are built ahead,
the people page left out because its build writes face groups into the index) and 0814
(cold open measured 2.9 s at 100,000 synthetic files with groups kept). Decided by the
maintainer in the review of 2026-11-13 (`feedback-2026-11-13-3-iterate`): warm it ahead.

## Proposal

- Build the people page's state on the warm-up thread (`first_warm`, low priority, after the
  others), kept by `kept_state` with the same key as a visit; the first click then reads it.
- Its build writes face groups (0588): the warm-up may write them, as a visit would; it never
  runs while an audit or `people` holds the index (skip, the visit builds it), and a failure is
  left for the visit, no traceback.
- Measure: first click before/after (`python -m tests.measure.pages.bench`, groups kept: a
  `--kept-groups` mode that copies an index whose groups are saved, asked in 0814's review),
  and the memory the kept state holds at 100,000 files (`tracemalloc`).

## Acceptance

- [ ] First click on the people page after a start: 2.9 s → under 0.1 s at 100,000 files, *measured*
- [ ] The bench's kept-groups mode, used for the figures
- [ ] A test: the warm-up skips while the index is being written, and its failure leaves the visit working
- [ ] Memory of the kept state written in the status
