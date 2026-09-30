# 0047 — `classify` crashes writing the workbook when a sheet has no row (no event)

- **Priority**: High — a traceback instead of a workbook, on any small library
- **Batch**: classify
- **Depends**: —
- **Files**: `src/media_hygiene/classify/workbook/writer.py`, `src/media_hygiene/classify/workbook/structure_rows.py`, `tests/unit/test_classify_workbook.py`

## Context

Seen while implementing 0046. `write_workbook` adds each drop-down validation and the auto-filter
on `A2:<col><rows + 1>`. When a sheet has no row — the Events sheet of a library where no event
reaches `min_event_size` (5 files), e.g. the integration demo tree built by `tests/support/demo.py`
after `clean` — the range is `J2:J1` and openpyxl raises
`ValueError: 1 must be greater than 2`. `classify` then ends with a traceback (the error is not a
`MountError`, so `_write_output` does not catch it), after printing the proposals; no plan, no
workbook, no report is written.

Reproduce: `make_plan().model_copy(update={"events": ()})` (from `tests/unit/test_classify_workbook.py`)
then `write_workbook(plan, tmp_path / "classify.xlsx")`.

## Proposal

- Skip the validations and the auto-filter of a sheet without rows (or give them the header row
  only), so that the sheet is written with its headers alone.
- Check that `sort` reads such a workbook back (`check_structure` / `keyed` with an empty sheet) and
  that the salvage of 0036 does too.

## Acceptance

- [ ] A plan without events (and one without categories) writes a workbook that `sort` accepts.
- [ ] A unit test covers it.
