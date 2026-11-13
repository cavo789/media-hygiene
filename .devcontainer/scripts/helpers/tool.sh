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
        # A bug shows its traceback here (MEDIA_HYGIENE_DEBUG=0 hygiene … shows the user's view)
        _gentle env "${env_vars[@]}" "MEDIA_HYGIENE_DEBUG=${MEDIA_HYGIENE_DEBUG:-1}" \
            uv run --frozen --quiet media-hygiene "$@"
    )
}

# @cat Tool
# @cmd home_dev
# @desc Home server from sources, restarted when src/ changes (templates are re-read live) — e.g. 'home_dev --port 8765'
function home_dev() {
    local root stamp pid changed
    root="$(_repo_root)" || return 1
    stamp="$(mktemp)"
    # Each round: one server in its own session (so the kill reaches uv's child); a changed
    # module ends it and the loop starts another, which draws a new RUN_TAG: the open tab
    # reloads itself (X-Media-Hygiene-Run). Templates need no restart (Jinja's auto_reload): the
    # variable makes every page poll their change time and reload itself (review/dev_reload.py).
    # shellcheck disable=SC2064
    trap "kill -- -\${pid:-0} 2>/dev/null; rm -f '${stamp}'; trap - INT TERM" INT TERM
    while :; do
        touch "${stamp}"
        MEDIA_HYGIENE_DEV_RELOAD=1 setsid bash -c 'hygiene home "$@"' _ "$@" &
        pid=$!
        changed=0
        while kill -0 "${pid}" 2>/dev/null; do
            sleep 0.5
            if [[ -n "$(find "${root}/src/media_hygiene" -name '*.py' -newer "${stamp}" -print -quit)" ]]; then
                echo "home_dev: source changed, restarting"
                kill -- "-${pid}" 2>/dev/null || true
                wait "${pid}" 2>/dev/null || true
                changed=1
                break
            fi
        done
        # The server ended by itself (Ctrl+C, a step chosen, a crash): stop here.
        ((changed)) || break
    done
    rm -f "${stamp}"
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

# @cat Tool
# @cmd demo_clean
# @desc Delete /tmp/media-hygiene (demo data, journal, quarantine, reports, cache)
function demo_clean() {
    rm -rf /tmp/media-hygiene
    printf "🧹 /tmp/media-hygiene deleted: the next 'demo' starts from scratch.\n"
}
