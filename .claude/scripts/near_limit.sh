#!/usr/bin/env bash
set -euo pipefail

# Lists the files close to the line cap, before a change makes them cross it.
#
# A split decided while planning is a new module; a split forced by the linter after the
# change is a rushed one. Run it on the files a TODO names (its `Files:` bullet) in
# /todo:run Phase 1, and before editing any file you are about to grow.
#
# Usage: near_limit.sh [file...]
#   NEAR_LIMIT  lines from which a file is listed (default 185)
#   LINE_CAP    the cap itself (default 200)
#   NEAR_LIMIT_IGNORE  paths without a cap, an extended regex (default ^tests/; empty: none)
#
# Output: one line per file at or above NEAR_LIMIT: "<lines>/<cap> <path>"; nothing when
# every file has room. Folders and missing files are skipped. Always exits 0.

near="${NEAR_LIMIT:-185}"
cap="${LINE_CAP:-200}"
ignore="${NEAR_LIMIT_IGNORE-^tests/}"

for file in "$@"; do
    [[ -f "${file}" ]] || continue
    if [[ -n "${ignore}" && "${file}" =~ ${ignore} ]]; then
        continue
    fi
    lines="$(wc -l <"${file}")"
    if ((lines >= near)); then
        printf '%s/%s %s\n' "${lines}" "${cap}" "${file}"
    fi
done
