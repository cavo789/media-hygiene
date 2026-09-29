# 0028 — `sort <workbook>`: validate strictly, move journaled, prove nothing was lost

- **Priority**: High
- **Batch**: sort
- **Depends**: 0024, 0027
- **Files**: `src/media_hygiene/cli/cmd_sort.py`, `src/media_hygiene/cli/app.py`, `src/media_hygiene/services/sort.py`, `src/media_hygiene/actions/sort.py` (new), `src/media_hygiene/actions/manifest.py` (new), `src/media_hygiene/actions/journaled.py`, `src/media_hygiene/actions/verify.py`, `src/media_hygiene/index/repository.py`, `src/media_hygiene/classify/workbook/`, `documentation/en/`, `documentation/fr/`

## Context

`sort` applies the plan that `classify` wrote (0027), as the person edited it: it moves files
into `<target>/<year>/<category>/`. It is the acting half of `classify`, as `clean` is for
`audit`, with the same safeguards: journal, `undo`, and a check just before each change.

## Proposal

**Find and validate the plan**:
- `sort <path to classify.xlsx>` takes a host or container path through `HostPathMapper`. The
  workbook may be a copy edited anywhere mounted: `sort` finds `plan.json` under `/reports` by
  the plan id in `_meta`.
- `sort` without argument takes the workbook of the latest classify run, as `undo` takes the
  latest run.
- **Structure**, all or nothing:
  - sheet names and order;
  - exact header rows;
  - the same row ids, each exactly once (matched by id, not by position);
  - every locked cell equal to `plan.json`;
  - the `_meta` fingerprint.

  The first difference refuses the **whole** file, with the sheet, cell, expected and found
  values, and a tip: undo the change in Excel, or restore a copy. 0036 later adds "or run
  `classify` again: your edits are carried over". Only the editable cells are read, as values.
- **What was read** is shown before the confirmation: "412 edits read; workbook saved on
  2 October at 14:32". A workbook edited but not saved is noticed there.
- **Edited values**: Windows-forbidden characters and names (`CON`, `NUL`, `COM1`…), trailing
  dots or spaces, `..` segments, path length. NFC normalisation. `/` is the sub-folder
  separator. Every destination must stay under the target root.

**Guards**, before anything moves:
- The same as `clean` (`CleanService.ensure_ready`): a persistent `/journal`, no `:ro` data
  mount, writable mounts.
- The target root must be on a **persistent** mount (not the container's own disk), and it
  must not be inside a protected folder. It may be the source itself (sorting in place, 0026):
  the files already in place are counted, not moved.
- Protected files are never moved. Then the summary and the confirmation, reusing the
  `confirm_clean` pattern and `--yes`. The summary gives *(as sorta's)*: files to move, into
  how many folders, their size, how many are already in place, how many go to "to check" and
  "to sort", how many source folders will be removed. An empty plan says plainly that there
  is nothing to do.

**Moves**:
- Each file is re-checked just before moving (size and mtime, as `verify.change_blocker`). A
  changed or missing file is skipped and reported; files not in the plan are untouched.
- Same device → `os.rename` (instant, atomic). Otherwise → `move_verified`
  (`actions/quarantine.py`).
- An existing target is never overwritten: add a ` (2)` suffix.
- Journaled through `JournaledChanges` with `Phase.SORT` / `ActionKind.MOVE` (0024).
- **Companions travel together**: sidecars (`scan/sidecars.py`), Live Photos (HEIC + MOV of the
  same name), RAW + JPEG twins. They go to the same folder, in the same journal run.
- **The index follows**: the row's path is updated after each move, so the next `audit` does
  not re-hash tens of thousands of files.
- **Source folders left empty are removed**, deepest first, journaled as
  `ActionKind.REMOVE_FOLDER` (0024) and recreated by `undo`. Sorting in place would otherwise
  leave hundreds of empty `Juillet 2016` folders behind.
  - A folder is empty when nothing is left but the files of `[sort] junk_files` (default
    `Thumbs.db`, `desktop.ini`, `.DS_Store`); those go to the quarantine first, journaled.
  - A folder holding anything else stays, and the summary says how many and why.
  - Protected and excluded folders, and the mount roots, are never removed.
  - `--keep-empty-folders` opts out.

**Interruption and resume**: 70,000 moves take a while, and a laptop sleeps.
- Ctrl+C finishes the current file, closes the journal, prints what is done and says "run the
  same command again to continue".
- Running `sort` again on the same plan skips the rows a previous run of **this plan** already
  moved (its journal says so) and counts them as done, not as missing files. The runs of one
  plan are undone together or one by one (`undo` takes the latest).

**Nothing lost, proven**: a manifest of the media under the source roots and the target root,
taken before the moves and again after.
- Every plan row is verified (target present, same size; SHA-256 when the move crossed devices).
- File count **and** byte count are equal before and after.
- It is shown as a closing summary and written to the run's report (`manifest.json`).

`undo` reverses a sort run (0024).

## Acceptance

- [ ] Integration on a synthetic tree in `tmp_path`: `classify` → edit the workbook → `sort` →
      manifest equal → `undo` → tree byte-identical to the start, emptied folders recreated.
- [ ] Idempotence: `classify` right after `sort` proposes nothing to move (separate target and
      in place).
- [ ] Interrupted run (a fake raising after N moves) then `sort` again: every row moved once,
      nothing reported missing.
- [ ] A folder left with only `Thumbs.db` is removed, `desktop.ini` quarantined; `undo`
      restores both.
- [ ] Each tampering is refused with a precise message: renamed sheet, moved column, deleted
      row, edited locked cell, foreign `plan.json`.
- [ ] Name collision, cross-device move, changed file, companions: one test each.
- [ ] e2e: `classify` with `:ro` mounts, `sort` read-write; sort guide en + fr (and the undo
      page: a sort run is undone like a clean run); `.po` translated.
