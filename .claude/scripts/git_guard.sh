#!/usr/bin/env bash
# PreToolUse hook (Bash): refuses the git commands the working method forbids.
#
# Reads the tool call on stdin (JSON, `tool_input.command`) and exits 2 — the call is
# blocked and the message below goes back to Claude — when a command would:
#   - `git stash`: another session may share the working tree (its edits vanish);
#   - `--no-verify`: skips the commit gate (a red gate was pushed this way once);
#   - `git push --force`/`-f`: rewrites a branch a peer or CI may hold;
#   - `git checkout -- <file>` / `git restore`: drops a peer's edit under it.
# Only commands are read: here-document bodies and quoted strings are dropped first, so a
# commit message or a file written through `cat <<EOF` may mention these words.
# Everything else passes (exit 0). No output on success.
set -o nounset
set -o errexit
set -o pipefail

input=$(cat)
if command -v jq > /dev/null 2>&1; then
  command_text=$(printf '%s' "${input}" | jq -r '.tool_input.command // empty' 2> /dev/null || true)
else
  command_text=$(printf '%s' "${input}" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("tool_input",{}).get("command",""))' 2> /dev/null || true)
fi
[[ -n "${command_text}" ]] || exit 0

# Commands only: drop here-document bodies, then quoted strings.
commands=$(printf '%s\n' "${command_text}" | awk '
  stop != "" { if ($0 == stop) { stop = "" }; next }
  match($0, /<<-?[[:space:]]*["\x27]?[A-Za-z_][A-Za-z0-9_]*["\x27]?/) {
    word = substr($0, RSTART, RLENGTH)
    sub(/^<<-?[[:space:]]*["\x27]?/, "", word); sub(/["\x27]$/, "", word)
    stop = word
  }
  { print }' | sed -E "s/'[^']*'//g; s/\"[^\"]*\"//g")

refuse() {
  printf '%s\n' "git guard: ${1}" >&2
  printf '%s\n' "Rule: .claude/rules/workflow.md (shared tree, commit gate). Do it another way: a worktree or 'git show REV:path' instead of stash; fix the gate instead of --no-verify; a new commit instead of --force; ask before discarding a file." >&2
  exit 2
}

# A git command starts a line or follows ; & | ( or a backtick — never a word of text.
git_at="(^|[;&|(\`])[[:space:]]*(sudo[[:space:]]+)?git[[:space:]]+(-C[[:space:]]+[^[:space:]]+[[:space:]]+)?"
while IFS= read -r line; do
  [[ -n "${line}" ]] || continue
  if [[ "${line}" =~ ${git_at}stash([[:space:]]|$) ]]; then
    refuse "'git stash' is forbidden here (another session may share this checkout)."
  fi
  if [[ "${line}" =~ ${git_at}(commit|push)([[:space:]]+[^[:space:]]+)*[[:space:]]+(--no-verify|-n)([[:space:]]|$) ]] \
    || [[ "${line}" =~ ${git_at}(commit|push)[[:space:]]+(--no-verify|-n)([[:space:]]|$) ]]; then
    refuse "'--no-verify' skips the commit gate: fix what it reports instead."
  fi
  if [[ "${line}" =~ ${git_at}push([[:space:]]+[^[:space:]]+)*[[:space:]]+(--force|-f|--force-with-lease)([[:space:]]|$|=) ]] \
    || [[ "${line}" =~ ${git_at}push[[:space:]]+(--force|-f|--force-with-lease)([[:space:]]|$|=) ]]; then
    refuse "a forced push rewrites a branch a peer or CI may hold."
  fi
  if [[ "${line}" =~ ${git_at}(checkout[[:space:]]+--[[:space:]]|restore[[:space:]]) ]]; then
    refuse "'git checkout -- <file>' / 'git restore' discards edits a peer session may own: ask first."
  fi
done <<< "${commands}"
exit 0
