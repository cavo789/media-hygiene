# 0390 — review-sort: "Sort this event now" moves one event's files, not the whole workbook

- **Priority**: Medium
- **Batch**: review-sort
- **Depends**: 0385, 0387
- **Files**: `src/media_hygiene/services/sort.py`, `src/media_hygiene/services/sort_inputs.py`, `src/media_hygiene/services/sort_guards.py`, `src/media_hygiene/review/sort_app.py`, `src/media_hygiene/review/sort_session.py`, `src/media_hygiene/review/templates/sort_review.html.j2`, `src/media_hygiene/review/templates/apply_now.html.j2`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/commands/review-sort.md`, `documentation/fr/commands/review-sort.md`, `documentation/en/commands/sort.md`, `documentation/fr/commands/sort.md`, `documentation/en/sort/11-name-events-in-the-browser.md`, `documentation/fr/sort/11-name-events-in-the-browser.md`

## Why

The maintainer, 2026-10-25, on event 23 of 1137 (a First Communion, proposal accepted): "can I
validate this event only, and not the others? Like *Apply the changes* when cleaning." Today
no: Enter records the choice for that event, but `sort` applies the **whole** workbook (every
event, undecided ones with classify's proposal; read in the `sort` options: workbook, `--yes`,
`--keep-empty-folders`, no scope). So the user cannot tidy a collection event by event, and
running `sort` early applies proposals never looked at (the trip of 0385).

## What

- A button **Sort this event now** (and its key, listed in the ⌨ panel) on the page: saves the
  choice if needed, shows what will move (from the destination line of 0387), asks, then runs
  `sort` restricted to the files of that event — same guards (no `:ro` mount, `/journal`
  needed: the page says what is missing instead of failing), same journal, same `undo`, same
  manifest, the cache following the moves.
- In the shared *Apply now* look (`apply_now.html.j2`); the result is read back (files at their
  new place) and shown, never "done" from memory.
- The event is then shown as **sorted** (its files in place) and skipped by U and *Only the
  events to decide*.
- The next `classify` sees those files already in place; the plan the page runs on stays valid
  for the other events (rows of the sorted event no longer move: check `sort` refuses nothing
  else of the plan afterwards, path-keyed files rewritten as in 0382).
- CLI: `sort --event <id>` (the same restriction), so the page and the console share it.
- Mounts: `mh review-sort` mounts the photos `:ro` today; a page that can move needs them
  writable + `/journal`: say in the TODO feedback what `mh` mounts (as `mh review` does for
  its apply).

## Tests

`sort --event` moves only that event's files, journals them, `undo` puts them back; the page's
endpoint refuses without `/journal` with a sentence; the event shown as sorted afterwards; a
second event then sorted in turn (two runs, two undos).
