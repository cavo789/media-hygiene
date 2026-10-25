# 0385 — An event choice never flattens the folders the user named: kept, or under the event's folder

- **Priority**: High — accepting a "sure" event today can empty the user's own folders into another one
- **Batch**: classify
- **Depends**: —
- **Files**: `src/media_hygiene/classify/workbook/edits.py`, `src/media_hygiene/review/sort_sure.py`, `src/media_hygiene/review/sort_views.py`, `src/media_hygiene/review/templates/sort_review.html.j2`, `tests/unit/test_classify_edits.py`, `documentation/en/commands/review-sort.md`, `documentation/fr/commands/review-sort.md`, `documentation/en/sort/05-review-the-proposal.md`, `documentation/fr/sort/05-review-the-proposal.md`, `documentation/en/sort/11-name-events-in-the-browser.md`, `documentation/fr/sort/11-name-events-in-the-browser.md`

## Why

Reported by the maintainer on `mh review-sort`, 2026-10-25: a one-week trip (2019-07-12..07-19,
1815 files) is one event; its files come from the maintainer's own folders
(`2019/Montenegro/Budva`, `…/Cetinje`, `…/Parc national du Lovcen`, `…/Dubrovnik`) and from the
daughters' (`2019/Photos Chloé`, `Manon 2023/dcim`). The page proposes `2019/Photos Chloé` (the
folder most files get, `WorkItem.proposal`) and marks it **✔ sure**, so `V` accepts it with the 84
other sure events.

Measured with `resolve()` on a three-row plan (rows in `Montenegro/Budva`, `Photos Chloé`,
`Manon 2023`, all `Band.SURE`, one event): without an edit each keeps its folder; with the event
edit `Enter`/`V` records (`EventEdit("", "Photos Chloé")`), **all three go to `Photos Chloé`**;
with a typed name and that category, the same (the name is ignored by `{year}/{category}`).
`_decide` applies an event edit to every row not `STAY`, including the sure rows of another folder
the user named.

## What (decided by the maintainer, 2026-10-25)

- An event choice (workbook Events sheet **and** the page: both go through `resolve`) moves the
  files that have no folder of the user's as today: bands to check / to sort, generic folders
  (`DCIM`, `Camera`), neighbours, person folders (their own fate: 0386).
- A sure row whose reason is `existing-folder` (a folder the user named) is **never flattened**:
  - event accepted as proposed (Enter / `V` without a new destination): it keeps its folder;
  - event given a destination (the folder field of 0387, e.g. `Vacances au Monténégro`): the
    destination becomes the **parent**, and the user's folders stay below it, by the part of
    their path under the deepest common parent of the event's user-named folders:
    `2019/Montenegro/Budva` → `2019/Vacances au Monténégro/Budva`, `…/Cetinje` →
    `…/Vacances au Monténégro/Cetinje`. An event with a single user-named folder: that folder
    becomes the destination itself (no `Budva/Budva`).
- A file edit still wins over everything (the user can move one such file on purpose).
- The page says it: "N files keep their own folder (Budva, Cetinje…)" in the destination line
  (0387), and the tiles of such files show their own destination.
- `sort_sure.sure_value`: unchanged rule; the batch's confirmation counts the files that move.
- Docs: the "What it is for" section of `review-sort` and step 5 (Events sheet) say that the
  user's own folders are kept under the event's folder.

## Open point

An event made of two user-named folders the user wants merged ("Noël chez Mamy" + "Noël 2020")
can no longer be merged by naming the event: a category rename or the Files sheet still does it.
Say it in step 5.

## Tests

One per case of `_decide`: user-named folder kept under an event edit; to-sort and generic rows
moved; file edit still wins; `STAY` untouched; the `V` batch over such an event moves only the
loose files (the three-row probe above as a test); a destination given → `Budva`, `Cetinje`
under it; a single user-named folder → no `Budva/Budva`.
