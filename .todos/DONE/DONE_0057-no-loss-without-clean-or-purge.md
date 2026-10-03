# 0057 — No loss without clean or purge: atomic no-overwrite moves, safe link undo, guarded junk and prune

- **Priority**: High — the maintainer's requirement: "this kind of software MUST GUARANTEE there is no loss"
- **Batch**: safety
- **Depends**: —
- **Files**: `src/media_hygiene/actions/no_overwrite.py`, `src/media_hygiene/actions/quarantine.py`,
  `src/media_hygiene/actions/sort_moves.py`, `src/media_hygiene/actions/restore.py`,
  `src/media_hygiene/actions/album_links.py`, `src/media_hygiene/actions/purge.py`,
  `src/media_hygiene/actions/sort_cleanup.py`, `src/media_hygiene/config/sort_settings.py`,
  `src/media_hygiene/report/index_page.py`, `src/media_hygiene/paths/mounts.py`,
  `src/media_hygiene/paths/tool_overlaps.py`, `src/media_hygiene/services/tool_mounts.py`,
  `src/media_hygiene/cli/`, `documentation/en/reference-safety.md`,
  `documentation/fr/reference-safety.md`, `README.md`, `README_FR.md`, `tests/`

## Context

Rule to hold in code and in the docs: **content is lost only by `clean` (exact duplicates, after a
byte comparison, the kept copy staying) and `purge` (empties the quarantine); everything else either
does not touch the files or is a verified, journaled, undoable move — never an overwrite, never a
delete.** A code review found these gaps:

1. **Check-then-act races.** `sort_moves.Relocator.move` checks `os.path.lexists(target)` then
   renames: a POSIX rename silently replaces a file created in between. `restore._move`,
   `_copy_back` and `path.touch()` rely on `reversal.blocker`'s earlier `exists()`.
   `quarantine.move_verified` uses `shutil.copy2`, which overwrites its target.
2. **Album link undo trusts `st_nlink`.** `album_links.link_blocker` removes an album name when
   `st_nlink > 1`; on Docker Desktop NTFS mounts that count is unverified (TODO 0041): a wrong count
   could delete the last name of a photo.
3. **`[sort] junk_files` is user-configurable**: a media or sidecar name there would make `sort`
   quarantine a photo without `clean`.
4. **`clean` must never delete the kept copy itself** (same inode through two paths).
5. **Tool mounts inside the photos.** `reports --prune` rmtrees folders named by the *content* of
   `summary.json`; `purge` rmtrees every folder of `/quarantine`; the quarantine, journal, cache or
   reports folder could be mounted inside (or around) a data folder.
6. Every other unlink / rmdir / rmtree / rename / replace / copy / write / link in `src/` must be
   inventoried with a verdict.
7. The docs do not say plainly what can lose content.

Added by the maintainer: an early, reassuring chapter in both READMEs and the docs listing the
commands that never change the photos (verified from the code, read-only mounts recommended), a
read-only marker in the CLI `--help`, and a test pinning that list.

## Proposal

- One primitive module `actions/no_overwrite.py` for every move/copy/restore of a user file:
  `renameat2(RENAME_NOREPLACE)` via ctypes; on ENOSYS/EINVAL/ENOTSUP/EXDEV an exclusive copy
  (`O_CREAT|O_EXCL`, copystat, fsync, full digest compared, then the source unlinked; on mismatch
  only the copy it created is removed); `O_EXCL` for a recreated empty file. EEXIST surfaces as the
  existing "the target exists" / "it already exists" refusal.
- Album undo removes a name only when the recorded original exists, is not the link path, and
  `os.path.samefile(link, original)`.
- `[sort] junk_files` refuses media/RAW/sidecar extensions and wildcards; quarantine-time check too.
- `clean`: keep (and test) the `samefile` refusal before a delete.
- `prune_reports` removes only direct children named like a report stamp that hold `summary.json`;
  `purge` only run-id-named folders; a startup refusal when a tool folder and a data folder are the
  same host folder or nested (unless the tool folder is in an excluded folder).
- Docs (en + fr) and READMEs: "What can lose content", the read-only guarantee; CLI help markers.

## Explicit NON-goals

- Protecting against hardware failure or changes made outside the tool (documented as the limit).
