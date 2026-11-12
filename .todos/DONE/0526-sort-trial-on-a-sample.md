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

## Status — PARTIAL (2026-11-06)

### Done
- `sort --trial SAMPLE` (`services/sort_trial.py`): `latest` (the latest month with dated
  photos), a month `YYYY-MM`, or a folder (host or container path); the plan is cut like
  `--event`, one journaled run, undoable on its own; the same `sort` without `--trial` then
  moves only the rest (rows already moved are skipped). Tests: `tests/integration/test_sort_trial.py`.
- 👉 What next after a trial: "looks right? Sort the rest with the same plan" + the undo line
  (`cli/sort_result.py`, split out of `cmd_sort.py`, 200-line cap). Docs EN/FR `commands/sort.md`.

### Not done
- The page side: a *Try on one month* button on the sort/Events page of `library`, then the
  → code work, not the maintainer's: listed in 0718 (2026-11-12)
  photos shown in their new folders.
  **Reason:** out of scope of this lot (needs the `photo-picking-pages` contract and an
  Apply-now-like offer); the console path exists first.
- The suggested "sort the rest" command is plain `sort` (latest workbook): a named workbook
  → code work, not the maintainer's: listed in 0718 (2026-11-12)
  argument is not carried into it.

## Closed by the inbox (2026-11-12)

Nothing left for the maintainer: each item above is answered (`→`); the code work left is
listed in 0718, the captures in 0717.
