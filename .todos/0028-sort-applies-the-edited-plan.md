# 0028 — `sort <workbook>`: validate strictly, move journaled, prove nothing was lost

- **Priority**: High
- **Batch**: sort
- **Depends**: 0024, 0027
- **Files**: `src/media_dedup/cli/cmd_sort.py`, `src/media_dedup/cli/app.py`, `src/media_dedup/services/sort.py`, `src/media_dedup/actions/sort.py` (new), `src/media_dedup/actions/manifest.py` (new), `src/media_dedup/actions/journaled.py`, `src/media_dedup/actions/verify.py`, `src/media_dedup/index/repository.py`, `src/media_dedup/classify/workbook/`, `documentation/en/`, `documentation/fr/`

## Context

`sort` applies the plan that `classify` wrote (0027), as the person edited it: it moves files
into `<target>/<year>/<category>/`. It is the acting half of `classify`, as `clean` is for
`audit`, with the same safeguards: journal, `undo`, and a check just before each change.

## Proposal

**Find and validate the plan**:
- `sort <path to classify.xlsx>` takes a host or container path through `HostPathMapper`. The
  workbook may be a copy edited anywhere mounted: `sort` finds `plan.json` under `/reports` by
  the plan id in `_meta`.
- **Structure**, all or nothing:
  - sheet names and order;
  - exact header rows;
  - the same row ids in the same order;
  - every locked cell equal to `plan.json`;
  - the `_meta` fingerprint.

  The first difference refuses the **whole** file, with the sheet, cell, expected and found
  values, and a tip (run `classify` again, or restore the file). Only the editable cells are
  read, as values.
- **Edited values**: Windows-forbidden characters and names (`CON`, `NUL`, `COM1`…), trailing
  dots or spaces, `..` segments, path length. NFC normalisation. `/` is the sub-folder
  separator. Every destination must stay under the target root.

**Guards**, before anything moves:
- The same as `clean` (`CleanService.ensure_ready`): a persistent `/journal`, no `:ro` data
  mount, writable mounts.
- The target root must be on a **persistent** mount (not the container's own disk), and it
  must not be inside a protected folder.
- Protected files are never moved. Then the summary and the confirmation, reusing the
  `confirm_clean` pattern and `--yes`.

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
- Source folders left empty are reported, not deleted (possible later option).

**Nothing lost, proven**: a manifest of the media under the source roots and the target root,
taken before the moves and again after.
- Every plan row is verified (target present, same size; SHA-256 when the move crossed devices).
- File count **and** byte count are equal before and after.
- It is shown as a closing summary and written to the run's report (`manifest.json`).

`undo` reverses a sort run (0024).

## Acceptance

- [ ] Integration on a synthetic tree in `tmp_path`: `classify` → edit the workbook → `sort` →
      manifest equal → `undo` → tree byte-identical to the start.
- [ ] Each tampering is refused with a precise message: renamed sheet, moved column, deleted
      row, edited locked cell, foreign `plan.json`.
- [ ] Name collision, cross-device move, changed file, companions: one test each.
- [ ] e2e: `classify` with `:ro` mounts, `sort` read-write; documentation en + fr; `.po`
      translated.
