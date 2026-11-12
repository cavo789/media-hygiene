# 0727 — Settings index: card ids for the burst and junk strictness rows

- **Priority**: Low
- **Batch**: home
- **Depends**: —
- **Files**: `src/media_hygiene/services/settings_rows.py`, `src/media_hygiene/review/templates/home_draw.js.j2`, `src/media_hygiene/review/templates/home.js.j2`

Follows DONE 0707 (`.todos/DONE/DONE_0707-home-cards-anchors-from-settings.md`, commit f0c6fd26): the settings index links open the exact home page card for 5 rows; the burst strictness rows (`BURST_KEYS`) and the junk strictness row have no card id yet.

Decided by the maintainer in the review of 2026-11-12.

## What

- Give those rows their `#space/card` id so the link opens, unfolds and scrolls to the card.

## Acceptance

- [ ] Test: every row of the settings index has a card id that exists on the home page (extend 0707's test).
