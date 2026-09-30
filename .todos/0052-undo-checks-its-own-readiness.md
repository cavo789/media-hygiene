# 0052 — `undo` checks its own readiness, not the one of `clean`

- **Priority**: Medium — a wrong command name in a refusal, and a refusal an undo does not need
- **Batch**: sort
- **Depends**: —
- **Files**: `src/media_hygiene/cli/cmd_undo.py`, `src/media_hygiene/services/undo.py`, `src/media_hygiene/services/acting.py`, `tests/integration/test_clean_undo.py`, `tests/integration/test_undo_sort.py`

## Context

`cli/cmd_undo.py` guards every undo with `CleanService(runtime, NullProgress()).ensure_ready()`,
whatever the run kind, although 0028 extracted the shared guard
`services/acting.ensure_can_act(runtime, command)` (used by `clean` and `sort`). Two effects:

- The `:ro` refusal says "Remove ':ro' from their -v options to let 'clean' act." while the
  user typed `undo` (a sort run's undo included).
- `ensure_ready` also refuses when `[scan] other_files = true` and `/quarantine` is not
  mounted ("Copies of other files than media go to /quarantine: mount it."). That rule is about
  what `clean` is going to move; an undo moves nothing to the quarantine. A sort run never used
  it, and a clean run that deleted only duplicates can be undone from the keepers.

## Proposal

- `cmd_undo.py` calls `ensure_can_act(runtime, "undo")` instead of `CleanService.ensure_ready()`.
- When the run to undo holds quarantine moves (clean run with broken files, orphans, near
  duplicates, burst shots, other files) and `/quarantine` is not persistent, refuse with a
  message naming the quarantine and the run, before touching anything (today the undo would
  report each file as skipped). Decide whether this belongs in `services/undo.py` (it reads the
  journal anyway).

## Acceptance

- [ ] Undo of a sort run on a `:ro` data mount: the tip names `undo`.
- [ ] `[scan] other_files = true`, no `/quarantine`: the undo of a sort run proceeds.
- [ ] Undo of a clean run whose journal holds quarantine moves, no `/quarantine`: clear refusal.
- [ ] Tests for the three cases; new strings translated; docs EN + FR if a message changes.

## Explicit NON-goals

- Changing the guards of `clean` or `sort`.
