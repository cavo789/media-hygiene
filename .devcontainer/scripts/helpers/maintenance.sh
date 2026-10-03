# .devcontainer/scripts/helpers/maintenance.sh
#
# Category "Maintenance" — recover after a crash, keep Docker tidy, watch the dependencies.
#
# Sourced by ../interactive.sh — no shebang, never executed directly.
# shellcheck shell=bash

# @cat Maintenance
# @cmd git_doctor
# @desc Check the git objects; 'git_doctor --fix' repairs the empty ones a crash leaves
function git_doctor() {
    (
        cd "$(_repo_root)" || return 1
        local -a empty
        mapfile -t empty < <(find .git/objects -type f -size 0)
        if ((${#empty[@]})); then
            printf "⚠️  %s empty object file(s) in .git/objects (left by a crash).\n" "${#empty[@]}"
            if [[ "${1:-}" != "--fix" ]]; then
                printf "   Run 'git_doctor --fix' to repair them from the working tree.\n"
                return 1
            fi
            # An empty object holds nothing: deleting it loses nothing. Its content is written
            # again from the files on disk, tracked or staged, then from the index's trees.
            rm -f "${empty[@]}"
            git ls-files --cached -z | xargs -0 git hash-object -w >/dev/null
            git write-tree >/dev/null || return 1
        fi
        if git fsck --no-dangling; then
            printf "✅ The repository is healthy.\n"
            return 0
        fi
        printf "❌ git fsck still reports errors: see above.\n" >&2
        return 1
    )
}

# @cat Maintenance
# @cmd docker_doctor
# @desc Is Docker healthy? Late output, leftover test containers and volumes, disk use
function docker_doctor() {
    docker info >/dev/null 2>&1 || {
        printf "❌ Docker does not answer: is Docker Desktop running?\n" >&2
        return 1
    }
    # After a reboot, Docker Desktop has been seen dropping the attached output written after
    # about a second. The tests and docs read `docker logs` instead, so they still work.
    if [[ "$(docker run --rm alpine sh -c 'sleep 2; echo late' 2>/dev/null)" == "late" ]]; then
        printf "✅ Attached output complete.\n"
    else
        printf "⚠️  Attached output cut after ~1 s: restart Docker Desktop.\n"
    fi
    printf "\nLeftovers of e2e/docs runs ('docker_clean' removes them):\n"
    docker ps --all --filter "ancestor=media-hygiene:latest" --format "  container {{.Names}} ({{.Status}})"
    docker volume ls --format "{{.Name}}" | grep -E '^media-hygiene-(e2e|docs)-' | sed 's/^/  volume    /' || true
    printf "\n"
    docker system df
}

# @cat Maintenance
# @cmd docker_clean
# @desc Remove the containers and volumes that e2e/docs runs left behind
function docker_clean() {
    local -a containers volumes
    mapfile -t containers < <(docker ps --all --quiet --filter "ancestor=media-hygiene:latest")
    ((${#containers[@]})) && docker rm --force "${containers[@]}" >/dev/null
    mapfile -t volumes < <(docker volume ls --format "{{.Name}}" | grep -E '^media-hygiene-(e2e|docs)-' || true)
    ((${#volumes[@]})) && docker volume rm "${volumes[@]}" >/dev/null
    printf "🧹 %s container(s) and %s volume(s) removed.\n" "${#containers[@]}" "${#volumes[@]}"
}

# @cat Maintenance
# @cmd deps
# @desc Direct dependencies with a newer release (e.g. pillow-heif for TODO 0054)
function deps() {
    (
        cd "$(_repo_root)" || return 1
        local outdated
        outdated="$(uv tree --outdated --depth 1 --frozen | grep 'latest:' || true)"
        if [[ -z "${outdated}" ]]; then
            printf "✅ Every direct dependency is up to date.\n"
            return 0
        fi
        printf "%s\n" "${outdated}"
    )
}
