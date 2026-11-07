# 0645 — The 🤖 local AI card on every page that uses it

- **Priority**: Low
- **Batch**: settings-on-pages
- **Depends**: —
- **Files**: `src/media_hygiene/review/setting_groups.py`, `src/media_hygiene/review/templates/`

## Problem

Follows 0608 (commit d1bf8ed2). The 🤖 card (found/absent, models, choice) is only in the tags
dialog of the home page.

## Decided (2026-11-06, maintainer, review of the iterate of 2026-11-06 (2))

Also on the other AI pages: the vision pick of landmarks, the subject rules.

## Acceptance

- [ ] Same card, same template, on each AI page — PARTIAL: the card is now one shared,
  self-contained template (`review/templates/ai_card.html.j2`, `window.mhAiCard(box)`), used by
  the tags dialog of the home page (it also fixed a key clash: the dialog's `aiOff` text
  replaced the action pill's). The two other AI pages do not exist yet: the vision pick of
  landmarks is console only (0641 adds its page: include `ai_card.html.j2` there) and the
  subject rules have no page. Remaining: include the template when those pages are made.
