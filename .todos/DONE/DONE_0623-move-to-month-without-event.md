# 0623 — Library: "Move to their month", the photos sorted without an event

- **Priority**: Medium
- **Batch**: search
- **Depends**: 0596
- **Files**: `src/media_hygiene/services/selection_move.py`, `src/media_hygiene/services/event_place.py`, `src/media_hygiene/search/`, `documentation/en/commands/library.md`, `documentation/fr/commands/library.md`

## Why

Maintainer, 2026-11-06: some photos have no event to name, or none worth creating. They come back at every *Not sorted yet*, and the only way out on the page is to invent an event. A file directly in `YYYY/YYYY-MM` already counts as sorted (`Sorting.SORTED`), but no button puts it there.

## What

Next to **📂 Move to an event…**, on the 🔎 Photos and 🗂 Events tabs: **Move to their month**, no name asked, no event folder created. Same path as a move to an event: below the target chosen (0596) or the file's root, year and month from the same date, journaled, undoable, read back. The tiles are shown first and the button states the count.

## Decided (2026-11-06, maintainer)

Photos of several months: each goes to its own month, whereas an event takes the earliest photo's month for all.

## Rules

- A photo without a date: left where it is and counted in the result, never guessed.
- A file already in its month: counted "already there", not moved.

## Also

`documentation/*/commands/library.md`, the *Not sorted yet* sentence names only `YYYY\YYYY-MM\<name>`: say that directly in the month counts too.

## Done when

- Tiles picked across two months end in their months, leave *Not sorted yet*, and undo puts them back (test).
- A file with no date stays, and the result says so (test).
- Both languages of the docs updated; `docs_screenshots` flagged as stale.
