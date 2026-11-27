# 0852 — tests_for.py maps a cli/ change to the tests that walk every --help

- **Priority**: Low
- **Batch**: tooling
- **Depends**: none
- **Files**: `.claude/scripts/tests_for.py`, `tests/unit/test_tests_for.py`

## Why (review of feedback-2026-11-27-iterate; noticed by a peer session)

`tests/integration/test_cli.py` walks every verb's `--help` through `build_app`, so it does not import `cmd_*.py`: a change there never selects it. PRs 89 and 90 failed in CI on that test only.

## Do

- A change under `src/media_hygiene/cli/` (or a `.po`) adds `tests/integration/test_cli.py` and `tests/unit/test_cli_help_types.py`, like templates add the page contract tests.
- A test in `tests/unit/test_tests_for.py`.
