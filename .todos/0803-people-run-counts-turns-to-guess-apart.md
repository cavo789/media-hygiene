# 0803 — People run: photos whose turn is still to guess counted apart from new photos

- **Priority**: Low
- **Batch**: people
- **Depends**: —
- **Files**: `src/media_hygiene/people/`, `src/media_hygiene/review/templates/`, `documentation/en/commands/people.md`, `documentation/fr/commands/people.md`

Follows 0725 (commit b7fc9d5c): the turn guess is cached by `people` (table `face_turns`,
schema 21). On the first `people` run after that version, the photos already analysed get a
turn-only job and are counted as "missing", like new photos (about 15 min on 4 workers,
*estimated* from step 48's 0.13 s per photo).

## Decided (2026-11-13)

By the maintainer, in the review of `feedback-2026-11-13-2-iterate` (PR #84): show them as a
separate count, "N photos whose turn is still to guess", apart from the new photos, in the
console line and on the people page's progress line.

## Acceptance

- [ ] The run and the page say both counts; a turn-only job never counts as a new photo (test).
- [ ] Docs EN + FR; French strings.
