# 0749 — What 0543 left: mh: try `docker run` first, check the port only when Docker refuses it

- **Priority**: Medium
- **Batch**: launcher
- **Depends**: —
- **Files**: `.todos/PARTIAL/PARTIAL_0543-mh-try-docker-run-first-port-check-on-failure.md`, `src/media_hygiene/cli/templates/mh_guards.ps1.j2`, `src/media_hygiene/cli/templates/mh.ps1.j2`, `src/media_hygiene/cli/templates/mh_menu.ps1.j2`, `src/media_hygiene/cli/templates/mh_lan.ps1.j2`, `src/media_hygiene/cli/templates/mh_guards.sh.j2`, `src/media_hygiene/services/launcher_guards.py`
- **Needs maintainer**: a Windows run of `mh --lan` (firewall lines)

Split from section 0543 of PARTIAL 0718 (`.todos/PARTIAL/PARTIAL_0718-code-left-in-partial-todos.md`), as decided by the maintainer in the review of 2026-11-12 (one TODO per remaining section). Source TODO: `.todos/PARTIAL/PARTIAL_0543-mh-try-docker-run-first-port-check-on-failure.md`.

## Left (as listed in 0718; the source TODO has the full wording)

- `mh --lan`: its "opening" / firewall lines are still said before the container starts

## How to proceed

- Check each item against the code first: some may be done already and only unticked (then say so and close them).
- File follow-ups for what is really left; every figure says *measured* or *estimated*; a new limit: say whether it should be a setting.
- Documentation EN + FR and French strings when something user-facing changes.
- Part of this needs the maintainer (see *Needs maintainer*): do the code part, leave the rest said in the report, never guess it.
