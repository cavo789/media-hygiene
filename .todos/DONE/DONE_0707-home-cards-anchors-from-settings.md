# 0707 — Settings index links open the exact home page card, unfolded

- **Priority**: Low
- **Batch**: settings-on-pages
- **Depends**: —
- **Files**: `src/media_hygiene/review/templates/home_draw.js.j2`, `src/media_hygiene/review/templates/home.js.j2`, `src/media_hygiene/services/settings_rows.py`

Decided by the maintainer on 2026-11-11, review of the iterate of 2026-11-10 (PR #77).

## Context

0670 (commit 00cd8edc) links each setting to its page; the home page's ones (local AI, phones,
scan scope, import steps, tiles) open the right space but not the card. Decided: an anchor per
card that scrolls to it and unfolds it.

## Acceptance

- [ ] Each home card reachable by `#<card>`, unfolded; the settings rows use them (test)
