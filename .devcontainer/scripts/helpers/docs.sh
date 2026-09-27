# .devcontainer/scripts/helpers/docs.sh
#
# Category "Documentation" — regenerate the screenshots and console outputs of documentation/.
#
# Sourced by ../interactive.sh — no shebang, never executed directly.
# shellcheck shell=bash

# @cat Documentation
# @cmd docs_screenshots
# @desc Refresh the screenshots and outputs of documentation/ — 'docs_screenshots [fr]'
function docs_screenshots() {
    # The captures come from the real image, built from the sources; the synthetic demo
    # library, the Docker volumes and the browser only live in /tmp and in Docker.
    build || return 1
    (
        cd "$(_repo_root)" || return 1
        uv run --frozen --quiet python -m tests.support.docs "$@"
    )
}
