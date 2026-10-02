# 0055 — A file name starting with "=" becomes a formula in the classify workbook and the CSV exports

- **Priority**: Low
- **Batch**: report
- **Depends**: —
- **Files**: `src/media_hygiene/classify/workbook/cells.py`, `src/media_hygiene/report/csv_export.py`, `src/media_hygiene/report/inventory_workbook.py`

## Context

Found while doing TODO 0032 (2026-10-02). openpyxl stores any string value starting with `=`
as a formula (`data_type = "f"`). `classify/workbook/cells.py` (`locked_cell`, `editable_cell`)
writes file and folder names as-is: a file named `=1.jpg` (valid on Windows and Linux) makes
`classify.xlsx` hold an invalid formula, which Excel reports as a damaged file to repair. The
inventory workbook (0032) already forces such cells back to text (`_cell` in
`report/inventory_workbook.py`).

CSV files have the related, classic issue: Excel evaluates a cell starting with `=`, `+`, `-` or
`@` when it opens `plan.csv` or `inventory.csv`. Low risk (the user's own file names), but a
name such as `-2019 trip.jpg` or `+1.jpg` may show `#NAME?` instead of the name.

## Proposal

- Workbook: one shared helper that sets `data_type = "s"` for text starting with `=` (reuse it
  in `cells.py` and `inventory_workbook.py`); a test writes `=1.jpg` and reads it back as text.
- CSV: decide whether to protect cells starting with `= + - @` (the usual fix prefixes a `'`
  or a tab, which changes the raw text for other readers of the file). Maintainer decision.

## Acceptance

- [ ] `classify.xlsx` with a file named `=1.jpg` opens in Excel without a repair prompt and shows
      the name.
- [ ] The CSV behaviour is decided and documented in a test.
