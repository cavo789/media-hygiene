# 0636 — Unwanted review: a photo set aside by hand keeps its decision when its reason is turned off

- **Priority**: Medium
- **Batch**: review
- **Depends**: —
- **Files**: `src/media_hygiene/review/`

## Problem

Follows 0537 (commits b2488167, 3a90c649). A photo set aside, then its reason turned off by the
strictness slider, stays listed for this run; at the next opening with the saved value, its
decision is dropped.

## Decided (2026-11-06, maintainer, review of the iterate of 2026-11-06 (2))

A choice made by hand never disappears by itself: the decision survives the reopening, and the
page shows the photo with it.

## Acceptance

- [ ] Set aside, reason turned off, page reopened: the photo is still listed with its decision (test)
- [ ] *Apply now* applies it; undoing the choice on the page removes it
