# 0687 — The journals and the user's choices are saved with `mh backup`, and undo survives a lost journal

- **Priority**: High
- **Batch**: safety-net
- **Depends**: —
- **Files**: `src/media_hygiene/services/cache_backup.py`, `src/media_hygiene/services/backup_archive.py`, `src/media_hygiene/services/backup_check.py`, `src/media_hygiene/services/cache_restore.py`, `src/media_hygiene/services/undo.py`, `src/media_hygiene/actions/quarantine.py`, `documentation/en/commands/backup.md`, `documentation/fr/commands/backup.md`, `documentation/en/reference-safety.md`, `documentation/fr/reference-safety.md`

Filed by the UX / speed / security review of 2026-11-10 (asked by the maintainer; analysis only, no code changed).

## Context

"Everything can be undone" rests on the **journal**: `undo` reads `/journal/<run>.jsonl`.
Read in `services/backup_archive.py` and `commands/backup.md` (2026-11-10): `mh backup`
saves the index and `/config` (settings, `people/`, `events/`) — **not the journals**, and
not the user's choices kept under `/reports` (`decisions.json`, `sort-decisions.json`) nor
the albums' list. `mh push` copies the photo folders only. So:

- The journal folder (`$HOME\media-hygiene\journal`, on `C:`) has **one copy**. `C:` lost
  or reinstalled while the photos and their quarantine live on `D:`: the quarantined files
  are still there, but `undo` cannot run; after a `sort` of 50,000 files, no way back to
  the former folders at all (a sort keeps nothing in the quarantine).
- `clean --delete` is undone by rebuilding from the kept copy **as the journal says**:
  without the journal, the names and places of the deleted copies are gone.
- Hours of review choices not yet applied are lost with `/reports`.

What helps already: a run's quarantine mirrors the photo folders (`<run>/c/Photos/x.jpg`,
`actions/quarantine.py`), so the place of each quarantined file can be read from its path.

## Proposal

1. **`mh backup` also takes**: every journal (small: one JSON line per action — measure
   the size on the maintainer's journals), the pending choices (`decisions.json`,
   `sort-decisions.json` of the latest reports), the albums' list; listed in
   `manifest.json`, read back and counted as the rest. Never `/lan` (the authority's key).
   `restore` puts back the journals that are missing, never over a newer one.
2. **A copy at the end of each writing run**: the run's journal is copied next to the
   quarantine it filled (`<quarantine>/<run>/journal.jsonl`) — the files and their way back
   travel together, on the same disk. A `sort`'s journal goes to the push target with the
   next `mh push`.
3. **`undo --from-quarantine <run>`** when the journal is missing: rebuild the moves from
   the mirror layout (or from the copy of point 2), shown first (*seeing first*), never
   over a file.
4. `reference-safety.md`: the sentence "Keep the journal folder" becomes "the journal is
   saved by `mh backup` and travels with the quarantine".

## Acceptance

- [ ] A backup → wipe of `/journal` → restore → `undo` of a clean and of a sort works
      (integration test on the demo tree, disk identical afterwards)
- [ ] `undo --from-quarantine` on a run whose journal is gone: every file back, proven
- [ ] The archive's growth measured on a real journal folder (maintainer's sizes, read-only)
- [ ] What happens when the quarantine moves to another drive letter: tested
- [ ] Docs EN + FR

## Where the user gains

Before: the way back of every clean and sort has 1 copy, on `C:`. After: 3 (the PC, with
the quarantine, off the PC with the backup), and a clean can be undone even without it.

## Status — PARTIAL (2026-11-10)

### Done

- `mh backup` archives every journal (`journal/<run>.jsonl`) and the choice files of `/reports`
  (`decisions.json`, `sort-decisions.json`, `phone-decisions.json`, `import-bursts.json`,
  `albums.json`, at its top or one folder down) with their SHA-256 in the manifest
  (`services/backup_extra.py`); `backup_check` accepts the `journal/` and `reports/` members.
- `restore` always puts back the journals and choice files that are missing, never over one
  there (`move_no_replace`), each read back against its digest; the console lists them.
- `undo <run> --from-quarantine` (`services/undo_orphan.py`, `cli/undo_orphan_flow.py`): the
  moves rebuilt from the quarantine's mirror layout, listed first, asked, never over a file,
  only into a mounted drive folder, each proven by its size read back; emptied folders removed.
  Refused while the journal exists.
- Tests (`tests/integration/test_journal_backup.py`): backup → wipe `/journal` → restore →
  undo of a clean (quarantine and `--delete`), disk identical; a newer journal never
  overwritten; from-quarantine back whole (but the empty file a clean deletes); a file at the
  place kept; the photos' drive under another letter: those files stay, said; the quarantine
  moved to another folder: still read.
- Docs EN + FR: `backup.md`, `undo.md`, `reference-safety.md`.

### Not done

- Point 2, a copy of the journal next to the quarantine (`<quarantine>/<run>/journal.jsonl`)
  and the sort's journal pushed to the target.
  **Reason:** every reader of a run's folder (purge census, the quarantine tiles, undo's
  emptied-folder removal, `--from-quarantine` itself) would take it for a file set aside: it
  needs its own place (e.g. a sibling `<run>.jsonl` beside the run folders, skipped by
  `_is_run_folder`) and a decision on it.
- The undo of a **sort** after backup → wipe → restore is not tested (only clean): the same
  journal file is restored, but no test runs a sort here.
- The archive's growth on the maintainer's real journal folder.
  **Reason:** needs his files (read-only measurement): a `mh-measure.ps1` step summing
  `$HOME\media-hygiene\journal\*.jsonl`.
- `docs_screenshots` should run (the `--help` capture of `undo.md`, the `backup` output).
