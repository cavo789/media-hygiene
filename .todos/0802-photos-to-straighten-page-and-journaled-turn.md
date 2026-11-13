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
