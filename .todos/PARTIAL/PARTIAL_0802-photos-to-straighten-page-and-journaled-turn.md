# 0802 — Photos to straighten: the page, the journaled turn, the entry points

- **Priority**: Medium
- **Batch**: people
- **Depends**: —
- **Files**: `src/media_hygiene/index/turn_rows.py`, `src/media_hygiene/actions/orientation_bytes.py`, `src/media_hygiene/actions/`, `src/media_hygiene/review/templates/pick_grid.js.j2`, `documentation/en|fr/`

Remainder of PARTIAL 0725 (`.todos/PARTIAL/PARTIAL_0725-straighten-photos-audit-page-and-lossless-write.md`):
the guesses are in the index (`TurnStore.proposed()`), the two-byte write is ready
(`with_orientation`); nothing is shown nor written yet.

## What

- The *Photos to straighten* page on the shared `pick_*` templates (skill
  `photo-picking-pages`), each tile shown turned, untick = refusal kept by path (follows
  `sort`/`undo`/renames: a `PATH_TABLES` table or the moves of `index/moves.py`); *Apply
  now* (`ApplyOffer`), the way back home, 🤖 where the YuNet guess is pasted.
- The journaled write: entry `pending` → write a temporary copy with `with_orientation`,
  atomic rename, read back, `done`; protected folders never written; `undo` writes the old
  code back and proves the file byte-identical (SHA-256 kept in the journal).
- `people`'s *What next* line when turns are proposed, a home card, docs EN + FR,
  `docs_screenshots` to run.

## Acceptance

- [ ] Apply then undo: file byte-identical (test).
- [ ] Refusals survive `sort`/`undo`/rename (tests).
- [ ] Docs EN + FR; French strings.

## Status — PARTIAL (2026-11-13)

### Done

- Refusals kept by path: `index/turn_refusals.py`, table `turn_refusals` (schema 22), a
  `PATH_TABLES` table: follows `sort`/`undo` moves and Explorer renames (`index.rematch`),
  leaves with a file gone (test `tests/unit/test_turn_actions.py`).
- The journaled write: `actions/turn_write.py` (`TurnExecutor`, phase and action `turn`):
  `pending` with the SHA-256 and code before (`JournalEntry.orientation`) and the SHA-256
  after, temporary copy, atomic rename only if the photo still holds what was read, read
  back, `done`. Undo (`actions/turn_undo.py`, `Reversal.UNTURN`): only while the photo holds
  what was written, old code written back proven by the SHA-256 before, old mtime back —
  byte-identical (test). A stopped `pending` turn is recognised as never done.
- `services/turn_apply.py`: the jobs (proposed − refused − protected/backup folders − not a
  JPEG) and the run (`ensure_can_act`, `new_run`). Nothing calls it yet: no entry point.

### Not done → TODO 0810

- The *Photos to straighten* page on the shared `pick_*` templates (each tile shown turned,
  untick = `TurnRefusals.refuse`, *Apply now* running `TurnService`, way back home, 🤖),
  `people`'s *What next* line, the home card, the menu entry, docs EN + FR,
  `docs_screenshots`.
  **Reason:** one session's scope (0803 in the same lot); the page is a full tile page
  (skill `photo-picking-pages`, its headless-browser check) and its server route; the
  write stays unreachable until it exists (Seeing first).
