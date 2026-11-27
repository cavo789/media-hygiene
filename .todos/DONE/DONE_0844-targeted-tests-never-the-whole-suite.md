# 0844 — Targeted tests never fall back to the whole suite

- **Priority**: High
- **Batch**: tooling
- **Depends**: none
- **Files**: `.claude/scripts/tests_for.py`, `.claude/scripts/stop_gate.sh`, `.claude/rules/workflow.md`, `.devcontainer/scripts/helpers/*.sh` (`tests_quick`)

## Why (maintainer, 2026-11-15)

Twice in one session the "quick" tests ran for over ten minutes on the maintainer's PC:

1. `pytest $(python3 .claude/scripts/tests_for.py)` with only new modules or templates
   changed: the script prints `no test found for: …` on stderr and nothing on stdout, so
   `pytest` gets no argument and runs **the whole suite** (5 500 tests).
2. `--depth 1` over a working tree with many changed files: 2 350 tests in 7 min,
   including `tests/e2e/test_sort_trial_browser.py` (a browser).

The maintainer wants the loop to run only what the change needs; CI runs the rest.

## What

- `tests_for.py` never lets an empty result reach `pytest`: when nothing is found, it
  prints the tests of the changed module's **package** (by folder name:
  `src/media_hygiene/person/x.py` → the tests importing any `media_hygiene.person.*`
  module), and a changed template (`*.j2`, `*.css`, `*.js`) maps to the tests reading
  its package's templates (`tests/unit -k page|shell|same_features|script_names` today,
  see `.claude/rules/pages.md`). If still nothing, it prints a harmless target (e.g.
  `--co -q tests/unit/test_slow_log.py`) and says so: never an empty line.
- Leave `tests/e2e/` out unless asked (`--e2e`): their marker skips them, but collecting
  and starting them still costs.
- A cap: over N test files (measure: say 40), print the list's size and stop with a
  non-zero exit, so the caller narrows it (`--depth 0`, a path) instead of waiting.
  Should N be a setting? No: a constant in the script (a developer tool).
- Measure before and after on the two cases above (time, number of tests), and say
  *measured*.
- Update `workflow.md` (the line added on 2026-11-15 about "no test found") once the
  script handles it.

## Done when

- `tests_for.py` with only a new module changed prints its package's tests, never an
  empty line; a test proves it.
- No e2e test is listed by default.
- The two cases above take under a minute here (measured).
