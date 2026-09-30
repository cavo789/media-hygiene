# 0046 — `classify` after `sort`: files sorted into "To check" are proposed elsewhere

- **Priority**: Medium
- **Batch**: classify
- **Depends**: —
- **Files**: `src/media_hygiene/classify/folders.py`, `src/media_hygiene/classify/signals.py`, `src/media_hygiene/classify/engine.py`, `tests/integration/test_sort.py`, `documentation/en/sort/07-sort.md`, `documentation/fr/sort/07-sort.md`

## Context

Seen while implementing 0028. `FolderRules.meaning()` returns nothing for any folder below a
"to check" band folder (`To check`, `À vérifier`): the names there are the tool's own guesses.
So once `sort` has moved an unconfirmed "to check" file into `2019/To check/Vacances`, the next
`classify` no longer sees `Vacances`: another rule decides, or none does, and the file is proposed
elsewhere (`2019/To check/Documents and screenshots` on the demo library, where the synthetic
pictures look like screenshots; `2019/To sort/<event>` otherwise). `sort` would then move it
again. Sure, "to sort" and undated files are idempotent (tested in 0028), and so are "to check"
files the user confirmed in the workbook (they become sure).

## Proposal

Decide what a re-run proposes for a file already in `<year>/To check/<category>/`:
- keep it in place, still "to check", when no rule reaches `sure` (its folder is the previous
  guess: a guess again, not a meaning); or
- leave it as today and document that unconfirmed "to check" files may move again.

The first option makes `classify` right after `sort` propose nothing to move in every band.

## Acceptance

- [ ] On the demo library: `classify` → `sort` (no edit) → `classify` proposes nothing to move.
- [ ] A file in `To check/X` still leaves it when a sure rule matches it.
- [ ] Sort guide step 7 (en + fr) says what happens to unconfirmed "to check" files.
