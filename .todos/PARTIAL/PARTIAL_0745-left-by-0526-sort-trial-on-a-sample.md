# 0745 — What 0526 left: Sort trial on one month before the whole library

- **Priority**: Low
- **Batch**: sort
- **Depends**: —
- **Files**: `.todos/DONE/0526-sort-trial-on-a-sample.md`, `src/media_hygiene/services/sort.py`, `src/media_hygiene/services/sort_inputs.py`, `src/media_hygiene/cli/cmd_sort.py`, `documentation/en/commands/sort.md`, `documentation/fr/commands/sort.md`

Split from section 0526 of PARTIAL 0718 (`.todos/PARTIAL/PARTIAL_0718-code-left-in-partial-todos.md`), as decided by the maintainer in the review of 2026-11-12 (one TODO per remaining section). Source TODO: `.todos/DONE/0526-sort-trial-on-a-sample.md`.

## Left (as listed in 0718; the source TODO has the full wording)

- The page side: a *Try on one month* button on the sort/Events page of `library`, then the
- The suggested "sort the rest" command is plain `sort` (latest workbook): a named workbook

## How to proceed

- Check each item against the code first: some may be done already and only unticked (then say so and close them).
- File follow-ups for what is really left; every figure says *measured* or *estimated*; a new limit: say whether it should be a setting.
- Documentation EN + FR and French strings when something user-facing changes.

## Status — PARTIAL (2026-11-13)

### Done
- The suggested "sort the rest" command now carries the named workbook (`sort "<workbook>"`;
  plain `sort` when none was given): `cli/sort_result.py` (`rest=`), `cli/cmd_sort.py`. Test in
  `tests/unit/test_sort_parts.py`; docs EN + FR `commands/sort.md`.

### Not done
- The page side: a *Try on one month* button on the sort/Events page of `library`, then the
  photos shown in their new folders.
  **Reason:** a new UI action on a tile page (photo-picking contract, *Apply now* offer, a server
  route running a trial sort, Chromium proof): a lot of its own, not safe to do unattended.
