# 0065 — Review page: start with four keys

- **Priority**: Low
- **Batch**: review-bursts
- **Depends**: —
- **Files**: `src/media_hygiene/review/templates/review.html.j2`, `src/media_hygiene/review/templates/review_board.css.j2`, `documentation/en/clean/10-review-bursts.md`, `documentation/fr/clean/10-review-bursts.md`

## Context

Filed from the 2026-10-10 usability review. The keyboard legend lists ten keys at once.
Most series only need one: → accepts the proposal already made.

## Proposal

- The legend shows **→** (accept the proposal, next), **S** (only the sharpest), **A**
  (keep every shot), **X** (keep nothing: the whole series aside, then next); the others
  under a "More keys" disclosure. X stays visible on purpose: the maintainer asked for it
  (2026-10-10), throwing a whole failed series away is a common, fast choice.
- First visit (remembered by `localStorage`, wrapped in try/catch): a one-line banner
  "The proposal is already made: → is enough when it suits you".

## Acceptance

- Screenshots regenerated (`docs_screenshots`), docs en and fr.
