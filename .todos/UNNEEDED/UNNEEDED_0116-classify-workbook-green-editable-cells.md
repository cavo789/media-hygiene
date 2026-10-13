# 0116 — `classify.xlsx`: editable cells in pastel green instead of yellow, and every "yellow" wording with them

- **Priority**: Low
- **Batch**: classify
- **Depends**: —
- **Files**: `src/media_hygiene/classify/workbook/cells.py`, `src/media_hygiene/classify/workbook/summary.py`, `src/media_hygiene/cli/classify_flow.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/unit/test_classify_workbook_text.py`, `tests/integration/test_sort_review_merge.py`, `documentation/en/reference-glossary.md`, `documentation/fr/reference-glossary.md`, `documentation/en/sort/`, `documentation/fr/sort/`, `documentation/en/commands/sort.md`, `documentation/fr/commands/sort.md`, `documentation/en/commands/review-sort.md`, `documentation/fr/commands/review-sort.md`

## Context

Review 0056 (2026-10-12): the maintainer checked `classify.xlsx` in Excel (white cells locked,
yellow cells editable) and asked for the editable cells in a light pastel green, their usual
convention for "you may write here". Decided: for every user, not an option.

## What to do

- `cells.py`: `_EDITABLE_FILL` from `FFF2CC` to a pastel green (e.g. `E2EFDA`, Excel's "Green,
  Accent 6, Lighter 80%"); check the contrast of black text and of the drop-down arrow.
- Every user-facing "yellow cells" → "green cells" / "cellules jaunes" → "cellules vertes":
  `summary.py` (sheet text), `classify_flow.py` (next-step line), the `.po` catalogue
  (`i18n_update`), then the documentation pages listed above in both languages
  (`grep -rli "yellow\|jaune" documentation README*.md`).
- Docstrings and comments that say "yellow cells" (`carry_plan.py`, `prefill.py`, `writer.py`,
  `cells.py`): reword to "editable cells" so the next colour change touches code only.
- Screenshots: none of the workbook today (0056 decided none); nothing to regenerate.
- Old workbooks stay readable: the reader keys on the column, never on the fill colour — check it.

## Explicit NON-goals

- `inventory.xlsx` (no editable cell); the `[yellow]` Rich markup of console warnings.

## Acceptance

- A new `classify.xlsx` shows its editable cells in pastel green; a workbook written by the
  previous version is still read by `sort` and the carry-over.
- `grep -rni "yellow cell\|cellules\? jaune" src documentation README*.md` finds nothing.

## Closed — UNNEEDED (2026-10-13)

Weighed again with what green loses: yellow is the common spreadsheet convention for "cell to
fill in", green often reads "validated / OK" (a green row could look already accepted), and the
change touches ~20 files and both languages of the docs. The maintainer keeps yellow.
