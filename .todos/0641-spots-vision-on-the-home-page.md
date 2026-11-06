# 0641 — 🤖 The vision pick of landmarks on the home page, photos shown first

- **Priority**: Low
- **Batch**: places
- **Depends**: —
- **Files**: `src/media_hygiene/services/`, `src/media_hygiene/review/templates/`

## Problem

Follows 0589 (commit f45b4248). `mh spots --vision` is console only (rules *Visible in web* and
*Seeing first*).

## Decided (2026-11-06, maintainer, review of the iterate of 2026-11-06 (2))

Keep clearing the GeoNames landmark when the model says none. Add the 🤖 action to the home page:
the photos it will ask about shown first, the count on the button, the progress followed in the
page.

## Acceptance

- [ ] 🤖 action on the home page, flagged as needing a local model, with the photos shown first
- [ ] Progress in the page; a stop keeps what was done
