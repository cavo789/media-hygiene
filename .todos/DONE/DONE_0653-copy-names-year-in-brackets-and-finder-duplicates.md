# 0653 — Copy names: a year in brackets is not a copy, a macOS Finder duplicate is

- **Priority**: Low
- **Batch**: keep-policy
- **Depends**: —
- **Files**: `src/media_hygiene/plan/copy_names.py`, `tests/unit/test_copy_names.py`

`looks_like_copy` decides one criterion of `KeepPolicy` ("not a copy name") and
`without_copy_marks` the name judged afterwards. Two wrong answers, **measured** on 2026-11-07
by calling the function directly:

- `Vacances (2019).jpg` → `True`: the `\(\d+\)$` pattern meant for Windows' `IMG (1).jpg` also
  matches a year, so a meaningfully named file loses the "not a copy name" tie-break, and
  `without_copy_marks` strips its year.
- `IMG_0001 2.jpg` → `False`: macOS Finder names a duplicate `<name> 2` (to check: its exact
  rule for further copies and other locales), not recognised.

Found while measuring Ollama delegation (`.claude/plans/ollama-delegation-report.md`, §5.3):
the local models listed none of these.

## Plan

1. Brackets: only small counters count as a copy mark — e.g. `\((\d{1,2})\)$` — or exclude
   four-digit numbers from 1900 to 2100. Pick the rule, keep `IMG (100).jpg` decided either way
   in a test.
2. Finder: a trailing ` <digits>` after a space counts only when the stem without it is itself
   a device-generated name (`IMG_0001`, `DSC01234`…), since `Vacances 2` or `Mariage 2019` are
   real names. Reuse the device-name rules of `plan/name_rules.py` if they fit.
3. Tests for each case above, positive and negative, in `test_copy_names.py`; check that
   `without_copy_marks` agrees.
