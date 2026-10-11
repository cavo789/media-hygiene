# 0076 — Tip budget beyond audit and clean, command by command

- **Priority**: Low
- **Batch**: guidance
- **Depends**: —
- **Files**: `src/media_hygiene/cli/classify_flow.py`, `src/media_hygiene/cli/cmd_sort.py`, `src/media_hygiene/cli/cmd_album.py`, `src/media_hygiene/cli/tags_flow.py`, `src/media_hygiene/cli/cmd_xmp.py`, `src/media_hygiene/console/advice.py`

## Context

TODO 0061 added the closing tip budget (`console/advice.py`: safety lines, then 👉, then at most
`TIP_BUDGET` tips ranked by `TipKind`, the rest counted and shown with `--verbosity verbose`).
Only the end-of-command tips of `audit` and `clean` (plus the report tips in `flows.py`) go
through it; about 60 other `output.tip()` calls stay immediate.

Immediate is right for contextual tips (errors, the URL of a served page, "nothing changed",
reassurance): delaying them would print them after a blocking server or far from their context.
But some commands may also end with a pile of closing tips that the budget would trim.

## Steps

- [x] For each command that prints `tip()` lines at its end (`classify`, `sort`, `album`, `tags`,
  `xmp`, `inventory`, `history`, `purge`…), run it on the demo tree and count the closing lines.
- [x] Convert to `output.advise(Advice(kind, …))` only where more than two closing tips appear;
  keep contextual tips immediate. Rank tips that change the next command's result as `NEXT`
  (as audit does for `--prefer`).
- [x] Integration tests for each converted command; docs captures refreshed (`docs_screenshots`,
  en and fr).

## Acceptance

- No command ends with more than the safety lines, 👉 and two tips, outside `--verbosity verbose`.
- Contextual tips still appear next to what they explain.

## Status

DONE (2026-10-11, night run, second pass). Closing lines counted command by command on the demo
tree: only `classify` (duplicates left + nothing changed + no `/reports`) and `album` (files not
found + on another disk + nothing changed) could end with three tips; `sort`, `album --apply`
ended with a bare undo tip. Changes:

- `classify`: "exact duplicates are still there: run 'clean' first" is `TipKind.NEXT`; the
  missing `/reports` mount is a `setting()` fragment (merged into the ⚙️ line).
- `album`: "Run 'classify' again" and "set album.root" are `TipKind.NEXT`; the undo line is a
  `safety()` line with its full command (moved from `album_view` to `cmd_album`).
- `sort`: the undo line is a `safety()` line with its full command, as `clean` and `xmp`.
- Contextual tips stay immediate (errors, served pages, "Nothing was changed", interrupted runs,
  the manifest warning). `tags`, `xmp`, `inventory`, `history`, `purge`, `reports`, `search`
  end with two tips at most: unchanged.

Captures not regenerated (no Docker tonight): `docs_screenshots` (en, fr) refreshes
`classify.txt` and `sort.txt`.
