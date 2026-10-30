# 0526 — Sort trial on one month before the whole library

- **Priority**: Low
- **Batch**: sort
- **Depends**: 0524
- **Files**: `src/media_hygiene/services/sort.py`, `src/media_hygiene/services/sort_inputs.py`, `src/media_hygiene/cli/cmd_sort.py`, `documentation/en/commands/sort.md`, `documentation/fr/commands/sort.md`

## Asked (maintainer, 2026-10-30)

UX brainstorm: "I never used sort, but why not".

## What

- `sort` (and its page) offers to run first on a sample: one month (the latest with photos)
  or one folder, then shows the result as photos in their new folders.
- 👉 What next: "looks right? run it on the rest" (the same plan minus what is done), or
  `mh undo` the trial.

## Done when

A trial moves only the sample (test), the rest follows with the same plan, the trial is one
undoable run.
