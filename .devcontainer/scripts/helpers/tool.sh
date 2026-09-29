# .devcontainer/scripts/helpers/tool.sh
#
# Category "Tool" — run media-hygiene from the sources, against /tmp/media-hygiene/ instead of mounts.
#
# Sourced by ../interactive.sh — no shebang, never executed directly.
# shellcheck shell=bash

# @cat Tool
# @cmd hygiene
# @desc Run the CLI from sources — e.g. 'hygiene audit'
function hygiene() {
    local -a env_vars
    mapfile -t env_vars < <(_media_hygiene_env)
    (
        cd "$(_repo_root)" || return 1
        env "${env_vars[@]}" uv run --frozen --quiet media-hygiene "$@"
    )
}

# @cat Tool
# @cmd demo
# @desc Generate sample media in /tmp/media-hygiene, then audit
function demo() {
    local -r data_dir="/tmp/media-hygiene/data"
    printf "🧪 Generating demo media in %s...\n" "${data_dir}"
    rm -rf "${data_dir}"
    (
        cd "$(_repo_root)" || return 1
        uv run --frozen --quiet python -m tests.support.demo "${data_dir}"
    ) || return 1
    hygiene audit "$@"
}
