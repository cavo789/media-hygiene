#!/usr/bin/env bash
set -euo pipefail

# Stop hook: before Claude hands the turn back, the files it left changed must pass the
# commit gate (pre-commit on those files only). A failure sends Claude back to fix it
# (exit 2, the failures on stderr); a second failure in a row lets the turn end, with a
# warning, so that a gate Claude cannot fix never traps the session.
#
# A clean working tree costs nothing: the usual case after a commit.
#
# Usage (from .claude/settings.json, "Stop" hook): stop_gate.sh, the hook JSON on stdin.
#   STOP_GATE_CONFIG  the pre-commit configuration (default .config/.pre-commit-config.yaml)

config="${STOP_GATE_CONFIG:-.config/.pre-commit-config.yaml}"
input="$(cat || true)"
again="$(python3 -c 'import json, sys
try:
    print(str(json.loads(sys.stdin.read() or "{}").get("stop_hook_active", False)).lower())
except ValueError:
    print("false")' <<<"${input}")"

cd "${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel)}"
[[ -f "${config}" ]] || exit 0

# Changed or new files that still exist (a deleted file has nothing to check).
mapfile -t files < <(git status --porcelain --untracked-files=all | awk '{print $NF}' |
    while read -r path; do [[ -f "${path}" ]] && printf '%s\n' "${path}"; done)
((${#files[@]})) || exit 0

if output="$(nice -n 19 pre-commit run --config "${config}" --files "${files[@]}" 2>&1)"; then
    exit 0
fi

failures="$(grep -v -E '\.\.\.(Passed|Skipped)$|\(no files to check\)' <<<"${output}" | tail -40 || true)"
if [[ "${again}" == "true" ]]; then
    printf '{"systemMessage": "Commit gate still failing on the changed files: fix before committing."}\n'
    exit 0
fi
printf 'The commit gate fails on the files changed (pre-commit --files). Fix it, then end the turn:\n%s\n' \
    "${failures}" >&2
exit 2
