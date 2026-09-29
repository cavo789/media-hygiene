# 0036 — `classify` carries the human edits of the previous proposal over; a refused workbook is salvaged

- **Priority**: High — hours of editing must never be lost
- **Batch**: classify
- **Depends**: 0027, 0028
- **Files**: `src/media_hygiene/classify/carry.py` (new), `src/media_hygiene/classify/workbook/`, `src/media_hygiene/services/classify.py`, `src/media_hygiene/cli/cmd_classify.py`, `src/media_hygiene/cli/cmd_sort.py`, `documentation/en/sort/`, `documentation/fr/sort/`

## Context

The user spends hours in `classify.xlsx` (0027): naming events, renaming categories, moving
files. A new `classify` writes a new plan and a new workbook, with a new plan id, and the edits
of the previous one are gone. That happens:
- after changing a setting to improve the proposal (`merge_gap_hours`, a calendar date, a rule
  of 0035): exactly what a user should be encouraged to do;
- when new photos arrive before the sort;
- when `sort` refuses a workbook whose structure was broken by accident (0028): its tip
  "run `classify` again" would throw the edits away.

[sorta](https://github.com/shinKatana0/sorta) keys its manual marks by path, and learnt the
cost: a drive letter that changed or a renamed folder lost every name typed by the user, so it
had to add a `relocate` command. Hence matching by content below.

## Proposal

- `classify` finds the latest classify run under `/reports` whose workbook holds edits not yet
  applied by a sort, and carries them over by default. `--carry-over <workbook>` names another
  one; `--no-carry-over` starts fresh. The console says it: "412 edits carried over from the
  proposal of 2 October 2026, 14:32".
- **Tolerant reading**, unlike `sort`: only the id column and the editable columns are read,
  found by their header, rows matched by id in any order. A workbook `sort` refused is read as
  far as its ids and editable columns can be found.
- **Matching** into the new plan:
  - file edits by content (the SHA-256 of the index), so a file renamed or moved meanwhile keeps
    its edit; the path as a fallback;
  - event edits (name, category) go to the new event that holds most of the old event's files;
    an old event split in two gives its edit to both parts, and the summary says so;
  - category renames and "confirm the to-check files" by the proposed category name.
- An edit that finds no target (file gone, category no longer proposed) is listed in the console
  and the report, never dropped silently.
- A carried edit counts as a human edit: sure band, reason "carried over".
- Edits a `sort` run already applied (its journal says so) are not carried: those files are in
  their place, and 0026 sees them as in place.
- The refusal message of `sort` (0028) tips: "run `classify` again: your edits are carried over".

## Acceptance

- [ ] Edit a workbook, change `merge_gap_hours`, `classify` again: file, event and category
      edits land on the new plan; a split event gets its edit in both parts; an edit whose
      file is gone is listed.
- [ ] A workbook with a deleted column or a renamed sheet (refused by `sort`) is salvaged.
- [ ] After a partial `sort`, the applied edits are not carried; the others are.
- [ ] Sort guide en + fr (improve the proposal without losing your work); `.po` translated.
