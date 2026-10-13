# 0127 — Carry-over: a `--year` / `--path` run keeps the edits outside its scope for later

- **Priority**: Medium — hours of naming events must never look lost after a narrowed run
- **Batch**: classify
- **Depends**: —
- **Files**: `src/media_hygiene/classify/carry.py`, `src/media_hygiene/classify/carry_types.py`, `src/media_hygiene/classify/carry_plan.py`, `src/media_hygiene/classify/plan_file.py`, `src/media_hygiene/services/carry.py`, `src/media_hygiene/console/carry_view.py`, `tests/integration/test_classify_carry.py`, `documentation/en/sort/05-review-the-proposal.md`, `documentation/fr/sort/05-review-the-proposal.md`

## Context

Review of the 2026-10-13 run (questions on 0115 and 0126). The previous workbook a run carries
over is simply the latest one (`services/classify_runs.latest_workbook`), whatever its scope. After
a full run where the user edited files of 2016, `classify --year 2015` (or `--path C:\Photos\2015`)
matches no row for them and lists every such edit as "not carried over (the file is gone)"
(`LostWhy.GONE`, `carry.py`). The edits still exist in the older workbook, but the next workbook
no longer holds them: a later full run carries from the `--year` workbook and loses them for good.
Since 0115, files dated only by the disk are also left out of `--year` runs, so their edits fall
in the same hole.

Decided with the maintainer (2026-10-13): **keep the rest for later**.

## What to do

1. A run with `--year` or `--path` carries over the edits of its own files as today.
2. The edits whose file (or event, or category) lies outside the run's scope are neither carried
   into the workbook rows nor listed as lost: they are kept as is, in the new plan
   (`plan.json`, e.g. a `deferred` list of `CarryRecord`-like entries, sheet + key + value), and
   the console says it in one line ("N edits of other years kept for a run without --year").
   An edit outside the scope is one whose file the scope excludes (other years, dated by the disk
   only, outside the `--path` folders) — not one whose file is really gone.
3. The next carry-over reads the previous workbook's edits **and** its plan's deferred edits;
   whatever the new run covers is applied, the rest is deferred again. A file really gone stays
   `LostWhy.GONE`.
4. Conflicts: a deferred edit and a newer workbook edit of the same file — the newer workbook wins
   and the deferred one is listed as replaced (same wording family as the review-page conflicts).
5. Docs en + fr (`sort/05-review-the-proposal.md`, the carry-over section): narrowed runs keep the
   other edits for later.

## Explicit NON-goals

- Choosing the previous workbook by scope (a workbook per year): the latest one stays the source.
- Carrying edits into `sort` itself (it applies the workbook it is given).

## Acceptance

- Integration test: full run, edit a 2016 file and a 2015 file; `classify --year 2015` carries the
  2015 edit, lists nothing as lost, says one edit is kept; a full run then carries both.
- Same with `--path`, and with a file dated by the disk only under `--year`.
- A file deleted between runs is still listed as gone.
