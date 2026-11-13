# 0734 — What 0423 left: CI: the Tests job is the critical path, its slowest tests first

- **Priority**: Low
- **Batch**: tests
- **Depends**: —
- **Files**: `.todos/DONE/0423-ci-tests-job-off-the-critical-path.md`, `.github/workflows/ci.yml`, `tests/integration/test_sort.py`, `tests/unit/test_launcher_comfort.py`, `tests/integration/test_places_tree.py`, `tests/integration/test_places_folders.py`

Split from section 0423 of PARTIAL 0718 (`.todos/PARTIAL/PARTIAL_0718-code-left-in-partial-todos.md`), as decided by the maintainer in the review of 2026-11-12 (one TODO per remaining section). Source TODO: `.todos/DONE/0423-ci-tests-job-off-the-critical-path.md`.

## Left (as listed in 0718; the source TODO has the full wording)

- Medians of the Tests vs e2e jobs over at least three green runs, and the decision to split
- Options left for the documentation library if the Tests job stays the critical path: a

## How to proceed

- Check each item against the code first: some may be done already and only unticked (then say so and close them).
- File follow-ups for what is really left; every figure says *measured* or *estimated*; a new limit: say whether it should be a setting.
- Documentation EN + FR and French strings when something user-facing changes.
- Part of this needs the maintainer (see *Needs maintainer*): do the code part, leave the rest said in the report, never guess it.

## Decided (2026-11-13)

By the maintainer, at the start of `/todo:iterate` of 2026-11-13: **split the Tests job** into
two parallel jobs (`tests/unit` and `tests/integration`), a small `coverage combine` job keeping
the 90 % threshold. Medians *measured* over the 6 last green runs of `main` (2026-11-12,
`gh run view --json jobs`): Tests 392 s, Image end-to-end tests 224 s. Expected: Tests ≈ 6.5 →
≈ 4 min (*estimated*: the longer half, then e2e becomes the critical path).
