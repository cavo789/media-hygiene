# 0050 — Companions: a human edit on any member of the group decides for the whole group

- **Priority**: Medium — today a file edit on a Live Photo's video or a RAW twin is silently ignored
- **Batch**: sort
- **Depends**: —
- **Files**: `src/media_hygiene/actions/sort_build.py`, `src/media_hygiene/classify/workbook/edits.py`, `src/media_hygiene/services/sort_inputs.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/sort/06-write-down-what-you-know.md`, `documentation/fr/sort/06-write-down-what-you-know.md`, `documentation/en/sort/07-sort.md`, `documentation/fr/sort/07-sort.md`, `tests/unit/test_sort_parts.py`, `tests/integration/test_sort.py`

## Context

Maintainer answer (2026-09-30) to a question of the 0028 run: "a human edit on ANY member wins for
the whole group". Today `actions/sort_build.py` groups the files sharing a folder and a stem
(`IMG_1.HEIC` + `IMG_1.MOV`, `IMG_2.CR2` + `IMG_2.JPG`), orders them photo > RAW > video, then
name, and the **leading** file's `Decision` gives the folder of all of them, whatever the others'
rows say. `classify/workbook/edits.py` resolves each row alone (precedence file > event >
category, a human edit becomes `Band.SURE`) and does not tell which decisions come from a human
edit. So a user who types a folder on the video row of a Live Photo sees the photo's proposal win.

## Proposal

- Let `Decision` say where it comes from (e.g. `source`: file edit, event/category edit, proposal)
  so that `sort_build` can choose among the members.
- Folder of a group, in this order:
  1. a **file edit** (Files sheet cell) on any member wins for the whole group;
  2. otherwise an event or category edit that reached any member (the leading one first, in the
     group's order, when several members carry one);
  3. otherwise the leading file's proposal (today's rule).
- **Conflict — decided here:** two members carrying **file edits that disagree** (different folders,
  or a folder and "(stay where it is)") make `sort` refuse the workbook before moving anything, like
  every other workbook problem: the message names the cells (sheet, row, file name) and asks to give
  the twins the same folder, or to clear all but one. A file edit is a direct, explicit statement;
  picking one silently would ignore the other. Equal file edits are not a conflict. Two members whose
  folders differ only through event/category edits (step 2) are not refused: the first one in the
  group's order wins, and `sort` shows one line per such group ("IMG_1.MOV follows IMG_1.HEIC").
- The band of the group follows the chosen decision (a human edit: sure).
- Docs (en + fr): the "Companions travel together" bullet of `sort/07-sort.md` and the file-column
  explanation of `sort/06-write-down-what-you-know.md` say which edit wins and when `sort` refuses.

## Explicit NON-goals

- No change to how companions are grouped (same folder, same stem, case-insensitive) or to sidecars.
- No change in `classify`: the workbook still shows one row per file.

## Acceptance

- [ ] A file edit on the video of a Live Photo moves photo and video to the edited folder.
- [ ] A file edit on the photo still wins when the video carries none.
- [ ] Two conflicting file edits in one group: `sort` refuses, naming both cells; nothing moves.
- [ ] Unit tests (`sort_build`) and one integration test; `i18n_update` done, French translated.
