# 0049 — `undo` of a sort run walks back through every run of the same plan

- **Priority**: Medium — a resumed sort is one operation for the user; undoing it run by run is error-prone
- **Batch**: sort
- **Depends**: —
- **Files**: `src/media_hygiene/cli/cmd_undo.py`, `src/media_hygiene/services/undo.py`, `src/media_hygiene/actions/runs.py`, `src/media_hygiene/actions/sort_resume.py`, `src/media_hygiene/cli/flows.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/sort/07-sort.md`, `documentation/fr/sort/07-sort.md`, `documentation/en/clean/09-undo-history-purge.md`, `documentation/fr/clean/09-undo-history-purge.md`, `tests/integration/test_undo_sort.py`

## Context

Maintainer answer (2026-09-30) to a question of the 0028 run: "a resumed sort is one operation for
the user". Today a sort interrupted (Ctrl+C, crash, refused file) and run again with the same
workbook leaves one journal per run, each tagged with the plan id (`JournalEntry.plan`, used by
`actions/sort_resume.py` to skip the rows already moved). `undo <run>` reverses one journal only;
`documentation/<lang>/sort/07-sort.md` tells the user to undo the runs one by one, the latest first
(`history` lists them). Undoing only the last run leaves the files of the earlier runs sorted, and
the folders they created in place.

## Proposal

- When the run given to `undo` (or the latest one by default) is a `sort` run, collect every sort
  run of the journal whose entries carry the same plan id and that is not fully undone yet.
- Show them in one list (run id, date, files moved, per run) and ask **one** confirmation (the
  `confirm` pattern of `clean`/`sort`: `--yes` skips it; no interactive terminal and no `--yes` →
  refuse with the tip, as `require_terminal` does).
- Undo them newest first (each through `undo_run`, so each journal records its own `undo` phase and
  the index follows each run), then show one outcome table summing them, with the skipped and failed
  files of every run.
- A `clean` run keeps today's behaviour (one run, no confirmation added).
- Decide and document what happens when an earlier run of the plan was already undone on its own
  (skip it, say so) and when a later run of the same plan exists after the one named (walk from the
  newest one of the plan, and say so, rather than leaving a later run's moves on top).

## Explicit NON-goals

- No `undo --plan <id>` option: the run id of any run of the plan is enough.
- No change to `history` beyond what the list needs (it already names the command of each run).

## Acceptance

- [ ] A sort interrupted then resumed (two runs, one plan) is undone by one `undo`, after one
      confirmation listing both runs; every file is back, byte- and mtime-identical.
- [ ] `undo` of a clean run is unchanged.
- [ ] The docs (en + fr) no longer say "one by one"; `i18n_update` done, French translated.
- [ ] Integration test in `tests/integration/test_undo_sort.py`.
