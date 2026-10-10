# 0063 — `media-hygiene status`: where am I?

- **Priority**: Medium
- **Batch**: guidance
- **Depends**: 0059
- **Files**: `src/media_hygiene/cli/` (new `cmd_status.py`), `src/media_hygiene/cli/app.py`, `src/media_hygiene/services/` (new `status.py`), `src/media_hygiene/index/repository.py`, `src/media_hygiene/actions/runs.py`, `src/media_hygiene/review/place.py`, `documentation/en/reference-commands.md`, `documentation/fr/reference-commands.md`

## Context

Filed from the 2026-10-10 usability review. The path spans days (audit, clean, check the
quarantine, review, purge, classify, sort). A user coming back a week later does not know
what is left, and has to remember run IDs for `undo` / `purge`.

## Proposal

- Read-only, no scan, about a second. It reads:
  - the index: date and figures of the last audit;
  - the journal: runs still undoable, with their command;
  - the quarantine: size and age; older than `[general] purge_hint_days` (30) → suggest
    `purge`;
  - `decisions.json`: burst series still to see; `sort-decisions.json` / last `plan.json`.
- Ends with **one** next step, as a full command (0059).
- Shown mounts missing → it says what it could not look at, never fails.

## Acceptance

- After `demo` + `clean`: `status` reports the quarantine (files, size, `undo …` line,
  `purge` once checked). Unit tests per state; docs en and fr.
