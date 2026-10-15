# 0168 — Flaky test: `test_no_describe_announces_no_work` (classify `--no-describe`)

- **Priority**: Medium
- **Batch**: tests
- **Depends**: —
- **Files**: `tests/integration/subjects/test_classify_subjects_wording.py`, `src/media_hygiene/services/classify_subjects.py`

## Context

On 2026-10-15, CI run 38707267878 (attempt 1, PR #5, Renovate: Dockerfile pins only, so
nothing the `Tests` job runs) failed on one test, 2021 others passing:

```
FAILED tests/integration/subjects/test_classify_subjects_wording.py::test_no_describe_announces_no_work
assert '7 samples not described yet (--no-describe)' in '🔒 Read-only: … cavo789/media-hygiene sort'
```

pytest truncated the output, so it is unknown what the line said instead (another count,
no line at all). The same day, `main` had another timing-dependent failure in `clean`,
fixed by PR #6 (copies and shots set aside moved in the same parallel stage): look for a
similar cause here, e.g. the `--sample 2` run's cache writes, or the order in which several
workers describe and count the samples.

## What to do

1. Reproduce: run the test in a loop (`for i in $(seq 50); do pytest -q … || break; done`),
   also under load (`stress`-like CPU load, or `PYTHON_CPU_COUNT=1`/`8`).
2. Print the full output on failure (assert with `result.output` as message) to see the
   real count.
3. Fix the cause in the code if the count depends on timing; only the test if its
   expectation is wrong.

## Acceptance

- 50 runs in a row pass locally; the cause is named in the commit message.
