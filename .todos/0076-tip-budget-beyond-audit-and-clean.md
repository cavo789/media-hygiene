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

- [ ] For each command that prints `tip()` lines at its end (`classify`, `sort`, `album`, `tags`,
  `xmp`, `inventory`, `history`, `purge`…), run it on the demo tree and count the closing lines.
- [ ] Convert to `output.advise(Advice(kind, …))` only where more than two closing tips appear;
  keep contextual tips immediate. Rank tips that change the next command's result as `NEXT`
  (as audit does for `--prefer`).
- [ ] Integration tests for each converted command; docs captures refreshed (`docs_screenshots`,
  en and fr).

## Acceptance

- No command ends with more than the safety lines, 👉 and two tips, outside `--verbosity verbose`.
- Contextual tips still appear next to what they explain.
