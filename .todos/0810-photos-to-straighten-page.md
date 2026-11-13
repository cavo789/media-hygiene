# 0810 — Photos to straighten: the page, its Apply now, the entry points

- **Priority**: Medium
- **Batch**: people
- **Depends**: —
- **Files**: `src/media_hygiene/services/turn_apply.py`, `src/media_hygiene/index/turn_refusals.py`, `src/media_hygiene/review/templates/pick_grid.js.j2`, `src/media_hygiene/cli/menu_catalog_*.py`, `documentation/en|fr/`

Remainder of PARTIAL 0802 (`.todos/PARTIAL/PARTIAL_0802-photos-to-straighten-page-and-journaled-turn.md`):
the refusals by path (`TurnRefusals`), the journaled write and its byte-identical undo
(`TurnService`, `TurnExecutor`, `Reversal.UNTURN`) are ready; nothing shows nor calls them.

## What

- The *Photos to straighten* page on the shared `pick_*` templates (skill
  `photo-picking-pages`, every gesture), each tile shown turned, untick =
  `TurnRefusals.refuse` (read back, shown); *Apply now* (`ApplyOffer`) runs
  `TurnService`; the way back home; 🤖 where the YuNet guess is pasted.
- `people`'s *What next* line when turns are proposed, a home card, the menu entry, docs
  EN + FR, `docs_screenshots` to run.

## Acceptance

- [ ] The page served has `id="applyNow"` once a turn is pending (test).
- [ ] A refusal on the page leaves the photo out of the next Apply (test).
- [ ] Docs EN + FR; French strings.
