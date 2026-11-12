# 0774 — What 0687 left: The journals and the user's choices are saved with `mh backup`, and undo survives a lost journal

- **Priority**: Medium
- **Batch**: safety-net
- **Depends**: —
- **Files**: `.todos/PARTIAL/PARTIAL_0687-journals-and-choices-saved-off-the-pc.md`, `src/media_hygiene/services/cache_backup.py`, `src/media_hygiene/services/backup_archive.py`, `src/media_hygiene/services/backup_check.py`, `src/media_hygiene/services/cache_restore.py`, `src/media_hygiene/services/undo.py`, `src/media_hygiene/actions/quarantine.py`

Split from section 0687 of PARTIAL 0718 (`.todos/PARTIAL/PARTIAL_0718-code-left-in-partial-todos.md`), as decided by the maintainer in the review of 2026-11-12 (one TODO per remaining section). Source TODO: `.todos/PARTIAL/PARTIAL_0687-journals-and-choices-saved-off-the-pc.md`.

## Left (as listed in 0718; the source TODO has the full wording)

- Point 2, a copy of the journal next to the quarantine (`<quarantine>/<run>/journal.jsonl`)
- The undo of a **sort** after backup → wipe → restore is not tested (only clean): the same
- A backup → wipe of `/journal` → restore → `undo` of a clean and of a sort works
- `undo --from-quarantine` on a run whose journal is gone: every file back, proven
- What happens when the quarantine moves to another drive letter: tested
- Docs EN + FR

## How to proceed

- Check each item against the code first: some may be done already and only unticked (then say so and close them).
- File follow-ups for what is really left; every figure says *measured* or *estimated*; a new limit: say whether it should be a setting.
- Documentation EN + FR and French strings when something user-facing changes.
