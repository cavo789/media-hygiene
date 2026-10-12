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
        _gentle uv run --frozen --quiet python -m tests.support.docs "$@"
    )
}

# @cat Documentation
# @cmd docs_build
# @desc Build the documentation site like CI (strict: broken links fail) into /tmp/media-hygiene/site
function docs_build() {
    (
        cd "$(_repo_root)" || return 1
        NO_MKDOCS_2_WARNING=true _gentle uv run --frozen --quiet --group docs \
            mkdocs build --config-file .config/mkdocs/mkdocs.yml "$@"
    )
}

# @cat Documentation
# @cmd docs_serve
# @desc Preview the documentation site, reloaded on every save — 'DOCS_PORT=8001 docs_serve'
function docs_serve() {
    (
        cd "$(_repo_root)" || return 1
        NO_MKDOCS_2_WARNING=true uv run --frozen --quiet --group docs \
            mkdocs serve --config-file .config/mkdocs/mkdocs.yml \
            --dev-addr "127.0.0.1:${DOCS_PORT:-8000}" "$@"
    )
}
