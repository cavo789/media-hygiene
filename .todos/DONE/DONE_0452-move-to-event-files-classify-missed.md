# 0452 — *Move to an event…* moves the photos added since the latest classify

- **Priority**: High
- **Batch**: search
- **Depends**: —
- **Files**: `src/media_hygiene/services/plan_newcomers.py`, `src/media_hygiene/services/group_sort.py`, `src/media_hygiene/services/group_sort_models.py`, `src/media_hygiene/services/rule_trial.py`, `src/media_hygiene/classify/plan_build.py`, `src/media_hygiene/search/templates/search.html.j2`, `documentation/en/commands/search.md`, `documentation/fr/commands/search.md`

## Why

The maintainer, 2026-10-28: 54 photos imported from the phone, audited, picked on the search
page, *Move to an event…* `Valkenburg (Pays-Bas)`: *Nothing to move: no run was made. 54
files are not in the latest classify run: run classify again to sort them.* The move is the
journaled sort of the latest classify plan's rows; files added since had none.

## What (done)

- The files the plan has no row for go through the classify engine (the rules of
  `config.toml`, as `rule_trial` does): root, date and stable id are the engine's, the folder
  the page's, no event. Their rows live **for this move only**: `plan.json` and its workbook
  are checked against each other cell by cell (`workbook/structure.py`), so neither changes.
- The journal keeps each move: `undo` puts it back; a second move finds it at its new place
  (`moved_targets`), no run.
- Still counted apart: a file the index does not know (*run an audit, then move them*).
- The dialog's *Nothing to move: no run was made.* became *Nothing moved: every file is
  already in its place, or stays where it is.*

## Left

- The dialog's destination line shows `2026\2026-10\<name>` without the root for such files
  (the view reads the plan's roots only); the move itself goes below the engine's root.
