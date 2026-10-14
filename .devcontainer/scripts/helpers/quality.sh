# .devcontainer/scripts/helpers/quality.sh
#
# Category "Quality" — the lint/type/test gate and the formatter. Everything runs through
# _gentle (lower priority, a share of the processors): see _common.sh.
#
# Sourced by ../interactive.sh — no shebang, never executed directly.
# shellcheck shell=bash

# @cat Quality
# @cmd check
# @desc Full gate: pre-commit hooks + tests with coverage
function check() {
    lint || return 1
    (
        cd "$(_repo_root)" || return 1
        printf "🧪 Running the test suite with coverage...\n"
        _gentle pytest --cov --cov-report=term-missing:skip-covered
    )
}

# @cat Quality
# @cmd lint
# @desc Pre-commit hooks only (ruff, mypy, pylint, shellcheck...), new files included
function lint() {
    (
        cd "$(_repo_root)" || return 1
        printf "🔍 Running pre-commit hooks...\n"
        # Tracked AND untracked (non-ignored) files: `--all-files` would only see what git
        # already tracks, silently skipping every new file.
        # The hooks that check the whole tree (mypy, duplicate-code) add them on this flag.
        # Stage manual: the duplicate-code checks too, left out of each commit.
        git ls-files --cached --others --exclude-standard -z |
            LINT_UNTRACKED=1 _gentle xargs -0 pre-commit run --config .config/.pre-commit-config.yaml \
                --hook-stage manual --files
    )
}

# @cat Quality
# @cmd format
# @desc Auto-fix: ruff format + ruff check --fix
function format() {
    (
        cd "$(_repo_root)" || return 1
        ruff format . && ruff check --fix .
    )
}

# @cat Quality
# @cmd tests
# @desc Run pytest — e.g. 'tests tests/unit -k keeper'
function tests() {
    (
        cd "$(_repo_root)" || return 1
        _gentle pytest "$@"
    )
}

# @cat Quality
# @cmd tests_quick
# @desc Only the tests importing the files changed — TESTS_DEPTH=1 widens, 'tests' runs all
function tests_quick() {
    (
        cd "$(_repo_root)" || return 1
        local -a selected
        mapfile -t selected < <(python3 .claude/scripts/tests_for.py --depth "${TESTS_DEPTH:-0}")
        if ((${#selected[@]} == 0)); then
            printf "🤷 No test imports the files changed: 'tests' runs the whole suite.\n"
            return 0
        fi
        printf "🧪 %d test file(s) for the files changed (the gate stays 'check')...\n" "${#selected[@]}"
        _gentle pytest "${selected[@]}" "$@"
    )
}
