# .devcontainer/scripts/helpers/_common.sh
#
# Private helpers shared by the other modules. Deliberately un-annotated (no @cat/@cmd): they are
# building blocks, not commands, so they never show up in the cheatsheet.
#
# Sourced by ../interactive.sh — no shebang, never executed directly.
# shellcheck shell=bash

# _repo_root — absolute path of the repository, whatever the current directory.
function _repo_root() {
    realpath "${INTERACTIVE_SCRIPTS_DIR}/../.."
}

# _gentle — run an external command with a lighter footprint: lower priority, pinned to a share
# of the processors (taskset: pylint and pytest size their pools from the affinity) and
# PYTHON_CPU_COUNT for Python's own pools, which the e2e and docs containers inherit. Long runs
# at full load crashed the WSL VM, and once the whole PC, on the maintainer's machine.
# DEV_CPUS overrides the share: default half the processors, at least 2.
function _gentle() {
    local -r total="$(nproc)"
    local cpus="${DEV_CPUS:-$((total / 2))}"
    ((cpus < 2)) && cpus=2
    ((cpus > total)) && cpus="${total}"
    nice -n 10 taskset --cpu-list "0-$((cpus - 1))" env PYTHON_CPU_COUNT="${cpus}" "$@"
}

# _media_hygiene_env — print the MEDIA_HYGIENE_*_DIR assignments that redirect every mount point of
# the tool to /tmp/media-hygiene/, so a local run never needs Docker mounts nor touches the repo.
function _media_hygiene_env() {
    local base="/tmp/media-hygiene"
    local kind
    for kind in data config journal quarantine reports cache; do
        mkdir -p "${base}/${kind}"
        printf 'MEDIA_HYGIENE_%s_DIR=%s/%s\n' "${kind^^}" "${base}" "${kind}"
    done
}
