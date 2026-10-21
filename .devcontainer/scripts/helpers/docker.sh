# .devcontainer/scripts/helpers/docker.sh
#
# Category "Docker image" — build the shipped image, inspect its layers, run the end-to-end tests,
# release a version.
#
# Sourced by ../interactive.sh — no shebang, never executed directly.
# shellcheck shell=bash

# @cat Docker image
# @cmd build
# @desc Build media-hygiene:latest
function build() {
    printf "🏗️  Building media-hygiene:latest...\n"
    # The local target names `media-hygiene` in the commands the tool suggests (TODO 0080).
    docker build --target local --tag media-hygiene:latest "$(_repo_root)"
}

# @cat Docker image
# @cmd release
# @desc Tag vX.Y.Z (pyproject version) and push it: CI publishes the image
function release() {
    (
        cd "$(_repo_root)" || return 1
        local version
        version="$(sed -n 's/^version = "\(.*\)"$/\1/p' pyproject.toml)"
        if [[ -z "${version}" ]]; then
            printf "❌ Cannot read the version from pyproject.toml\n" >&2
            return 1
        fi
        local -r tag="v${version}"

        if [[ -n "$(git status --porcelain)" ]]; then
            printf "❌ Uncommitted changes: commit them first, the tag must match main\n" >&2
            return 1
        fi
        if git rev-parse --quiet --verify "refs/tags/${tag}" >/dev/null; then
            printf "❌ %s already exists: bump the version in pyproject.toml first\n" "${tag}" >&2
            return 1
        fi
        git fetch --quiet origin main || return 1
        if [[ "$(git rev-parse HEAD)" != "$(git rev-parse origin/main)" ]]; then
            printf "❌ HEAD is not origin/main: push main (or pull) first\n" >&2
            return 1
        fi

        # CI builds amd64 + arm64, runs the end-to-end tests, then pushes :<version> and :latest.
        git tag --annotate "${tag}" --message "media-hygiene ${version}" || return 1
        git push origin "${tag}" || return 1
        printf "✅ %s pushed: follow the publication in the repository's Actions tab\n" "${tag}"
    )
}

# @cat Docker image
# @cmd dive
# @desc Explore image layers with dive
function dive() {
    _dive_archive --tty
}

# dive 0.13.1 reading `docker://` from Docker 29 extracts nothing and exits 0 (2026-10-21):
# the gate passed without a look. It reads the saved archive instead, through a volume
# (docker-outside-of-docker: no host path is shared with the devcontainer).
# Usage: _dive_archive <docker run option> [dive arguments...]
function _dive_archive() {
    local -r volume="media-hygiene-dive"
    local -r run_option="$1"
    shift
    docker volume create "${volume}" >/dev/null || return 1
    docker save media-hygiene:latest |
        docker run --rm --interactive --volume "${volume}:/work" --entrypoint sh \
            wagoodman/dive:latest -c 'cat > /work/image.tar'
    local status=$?
    if ((status == 0)); then
        docker run --rm --interactive "${run_option}" --volume "${volume}:/work" \
            wagoodman/dive:latest docker-archive:///work/image.tar "$@"
        status=$?
    fi
    docker volume rm "${volume}" >/dev/null
    return "${status}"
}

# @cat Docker image
# @cmd dive_ci
# @desc Fail if the image wastes space (dive CI)
function dive_ci() {
    # Thresholds are flags rather than a .dive-ci file: a file would have to be bind-mounted from
    # a host path, which docker-outside-of-docker makes awkward. The ~2.2 % of "user" waste is
    # inherited from the official python image's own layers (debconf/dpkg files rewritten by its
    # apt steps), not from ours — 3 % keeps the gate strict on everything this Dockerfile adds.
    local -r lowest_efficiency=0.98
    local -r highest_user_wasted_percent=0.03
    _dive_archive --env=CI=true \
        --lowestEfficiency "${lowest_efficiency}" \
        --highestUserWastedPercent "${highest_user_wasted_percent}"
}

# @cat Docker image
# @cmd e2e
# @desc Build, then run the end-to-end tests (output kept in /tmp/media-hygiene/e2e.log)
function e2e() {
    build || return 1
    (
        cd "$(_repo_root)" || return 1
        # Kept for a rare failure (TODO 0053): the next run overwrites it.
        local log="/tmp/media-hygiene/e2e.log"
        mkdir -p "${log%/*}"
        _gentle pytest -m e2e "$@" 2>&1 | tee "${log}"
        return "${PIPESTATUS[0]}"
    )
}
