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
        git ls-files --cached --others --exclude-standard -z |
            _gentle xargs -0 pre-commit run --config .config/.pre-commit-config.yaml --files
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
