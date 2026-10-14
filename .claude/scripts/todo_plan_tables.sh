#!/usr/bin/env bash
set -euo pipefail

# Prints the mechanical parts of .todos/plan.md, so that /todo:plan (or a /todo:run between
# two lots) never recounts them by hand: the counts line of the header and the table of the
# PARTIAL TODOs. The lots, Standalone order and anomalies stay /todo:plan's judgement.
#
# Usage: todo_plan_tables.sh [todos-dir]
#   todos-dir  defaults to ./.todos
#
# Output (markdown):
#   > Open TODOs: N — Critical: n · High: n · Medium: n · Low: n · Locked: n · Waiting: n
#   (blank line)
#   | ID | Title | File |   ← one row per .todos/PARTIAL/PARTIAL_*.md, by ID

todos_dir="${1:-.todos}"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

records="$("${script_dir}/todo_parse_backlog.sh" "${todos_dir}")"
count() { grep -c -E "$1" <<<"${records}" || true; }

printf '> Open TODOs: %s — Critical: %s · High: %s · Medium: %s · Low: %s · Locked: %s · Waiting: %s\n' \
    "$(count '^ID: ')" "$(count '^PRIORITY: critical')" "$(count '^PRIORITY: high')" \
    "$(count '^PRIORITY: (medium|\(missing\))')" "$(count '^PRIORITY: low')" \
    "$(count '^LOCKED: .')" "$(count '^NEEDS: .')"
printf '\n| ID | Title | File |\n|----|-------|------|\n'
shopt -s nullglob
for file in "${todos_dir}"/PARTIAL/PARTIAL_*.md; do
    first_line="$(head -1 "${file}")"
    id="$(sed -E 's/^#[[:space:]]+([^[:space:]]+).*/\1/' <<<"${first_line}")"
    title="$(sed -E 's/^#[[:space:]]+[^[:space:]]+[[:space:]]*(—|-)[[:space:]]*//' <<<"${first_line}")"
    name="$(basename "${file}")"
    printf '| %s | %s | [%s](PARTIAL/%s) |\n' "${id}" "${title}" "${name}" "${name}"
done
