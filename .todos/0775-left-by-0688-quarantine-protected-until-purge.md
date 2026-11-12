# 0775 — What 0688 left: The quarantine is covered by the NAS copy, or `purge` says what has no other copy

- **Priority**: Medium
- **Batch**: safety-net
- **Depends**: —
- **Files**: `.todos/DONE/0688-quarantine-protected-until-purge.md`, `src/media_hygiene/services/push_sources.py`, `src/media_hygiene/services/push_listing.py`, `src/media_hygiene/services/push_lines.py`, `src/media_hygiene/services/quarantine_ledger.py`, `src/media_hygiene/actions/purge.py`, `src/media_hygiene/services/disk_purge.py`

Split from section 0688 of PARTIAL 0718 (`.todos/PARTIAL/PARTIAL_0718-code-left-in-partial-todos.md`), as decided by the maintainer in the review of 2026-11-12 (one TODO per remaining section). Source TODO: `.todos/DONE/0688-quarantine-protected-until-purge.md`.

## Left (as listed in 0718; the source TODO has the full wording)

- The figure on the quarantine page, the disk-space page and in `mh push`'s lines.
- A NAS copy counted as cover.
- The only copies are asked after the general purge question, not shown before it.
- The count of only-copy files shown before a purge, proven on the demo tree (a near
- With A: a push after a clean copies the run's quarantine; after a purge it leaves
- Docs EN + FR (`push.md`, `purge.md`, `reference-safety.md`)

## How to proceed

- Check each item against the code first: some may be done already and only unticked (then say so and close them).
- File follow-ups for what is really left; every figure says *measured* or *estimated*; a new limit: say whether it should be a setting.
- Documentation EN + FR and French strings when something user-facing changes.
