# 0126 — `classify --path`: only the files below a folder, like `tags` and `people`

- **Priority**: Low
- **Batch**: classify
- **Depends**: —
- **Files**: `src/media_hygiene/cli/cmd_classify.py`, `src/media_hygiene/services/classify.py`, `src/media_hygiene/cli/cmd_tags.py`, `documentation/en/commands/classify.md`, `documentation/fr/commands/classify.md`, `tests/integration/`

## Context

Review 0056 (2026-10-12): the maintainer typed `mh classify --path "C:\Photos\2015"` by reflex —
`tags` and `people` accept `--path` (host folders, as mounted) — and got "No such option".
`classify` only scopes by `--year`. Decided: add `--path`.

## What to do

- `--path` (repeatable), same help, same host → container mapping as `cmd_tags.py`
  (`runtime.mapper.to_container`); refused cleanly when the folder is not under a mount.
- Semantics to settle and write in the help: events are still built from **every** file (an
  event crossing the folder boundary stays whole, like `--year` keeps an event in the year of its
  start), and only the files below the folders get a proposal and a row in the workbook. Combine
  with `--year` as an intersection.
- The carry-over of a previous workbook ignores rows outside the scope, as it does for `--year`
  (check `carry_*`).
- Docs: options table and `--help` capture of `commands/classify.md`, en + fr.

## Explicit NON-goals

- `--path` on `sort` (it applies the workbook it is given).

## Acceptance

- `classify --path C:\Photos\2015` proposes only files below that folder (integration test with
  two folders); with `--year`, the intersection.
- A folder outside every mount is refused with the same message as `tags --path`.
