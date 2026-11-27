#!/usr/bin/env bash
set -euo pipefail

# Prints every TODO of the backlog, one line each: ID<TAB>STATUS<TAB>title, sorted by ID.
#
# The anti-duplication step of the todo-authoring skill and /todo:add read it instead of listing
# files by hand. STATUS is OPEN for the flat backlog, else the status subfolder's name (DONE,
# PARTIAL, BLOCKED, UNNEEDED, POSTPONED, ...). Hidden folders are pruned, like todo_next_id.sh;
# the ID is the first digit run of the file name, whatever its status prefix; the title is the
# first line without its `# NNNN —` head.
#
# Usage: todo_known_ids.sh [todos-dir] [--open]
#   todos-dir  defaults to ./.todos
#   --open     the flat backlog only

todos_dir=".todos"
max_depth=2
for arg in "$@"; do
    case "${arg}" in
    --open) max_depth=1 ;;
    *) todos_dir="${arg}" ;;
    esac
done
[[ -d "${todos_dir}" ]] || exit 0

find "${todos_dir}" -mindepth 1 -maxdepth "${max_depth}" -name '.*' -prune -o -type f -name '*.md' -print |
    while IFS= read -r file; do
        name="$(basename "${file}")"
        id="$(sed -nE 's/^[^0-9]*([0-9]{3,}).*/\1/p' <<<"${name}")"
        [[ -n "${id}" ]] || continue
        folder="$(basename "$(dirname "${file}")")"
        status="OPEN"
        [[ "$(dirname "${file}")" == "${todos_dir%/}" ]] || status="${folder^^}"
        title="$(head -1 "${file}" | sed -E 's/^#[[:space:]]*//; s/^[0-9]+[[:space:]]*(—|-)?[[:space:]]*//')"
        printf '%s\t%s\t%s\n' "${id}" "${status}" "${title}"
    done | sort -n -k1,1
