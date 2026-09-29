# 0024 — Journal: record which command made a run; undo refuses unknown actions

- **Priority**: High — prerequisite of `sort` (0028); the undo gap is a latent data-loss bug
- **Batch**: journal
- **Depends**: —
- **Files**: `src/media_hygiene/constants.py`, `src/media_hygiene/actions/kinds.py` (new), `src/media_hygiene/actions/journal.py`, `src/media_hygiene/actions/journaled.py`, `src/media_hygiene/actions/undo.py`, `src/media_hygiene/actions/runs.py`, `src/media_hygiene/cli/cmd_history.py`, `src/media_hygiene/cli/cmd_undo.py`, `documentation/en/09-undo-history-purge.md`, `documentation/fr/09-undo-history-purge.md`

## Context

The journal and `undo` were written for `clean` only. A second acting command (`sort`, which
moves files into a `year/category` tree) would hit two gaps:

- **Undo recreates an empty file for an action it does not know.** `undo._source_of` returns
  `None` for any `ActionKind` outside `QUARANTINED` and `DELETE_DUPLICATE`, and `_rebuild` then
  calls `path.touch()`. That is right for `DELETE_EMPTY` only. For a move, the "restored" file
  would be 0 bytes while the real one stays at its new place.
- **Nothing says which command made a run.** `Phase.CLEAN` is hard-coded in
  `JournaledChanges.entry`, `UndoExecutor` only reverses `Phase.CLEAN` entries, and
  `runs.summarize` counts anything not quarantined as "deleted / freed". A sort run would show
  in `history` as a clean that deleted everything it moved.

## Proposal

- `Phase` already means "which command wrote the entry": add `Phase.SORT`. The context of
  `JournaledChanges` carries the phase instead of hard-coding it. Older journals keep reading as
  `clean`.
- New `ActionKind.MOVE` with a new optional `target` field on `JournalEntry` (older journals
  still load: the field defaults to `None`).
- New `ActionKind.REMOVE_FOLDER`: `sort` removes the source folders it leaves empty (0028);
  `undo` recreates them (before moving their files back). Defined here so that 0028 only uses
  the vocabulary.
- `constants.py` is at the 200-line limit: move the journal enums (`ActionKind`, `Phase`,
  `Status`) to `actions/kinds.py` first, in a commit of their own (pure move, no behavior
  change), then add the new members.
- `_source_of` becomes an explicit match on every `ActionKind`:
  - `DELETE_EMPTY` keeps its "recreate empty" behavior, now explicitly;
  - `MOVE` is reversed from `target`, as a verified move back (same `sha256` check as today);
  - an unknown kind raises `JournalError`: never touch, never guess.
- `UndoExecutor` reverses the action phase of the run (clean or sort), and removes the folders a
  sort created once they are empty again.
- A moved file that is no longer at its `target` (the user moved or renamed it by hand after
  the sort) is **skipped and reported**, never searched for: the rest of the run is undone.
  Same for a `target` whose SHA-256 no longer matches.
- `sort` needs to know which entries of a run are `done` to resume an interrupted run (0028):
  expose that from the journal reader.
- `RunSummary` gains the run kind and a `moved` counter. `history` shows a "Command" column and
  is titled "Runs". `undo` without a run id names the kind of the run it reverses.

## Acceptance

- [ ] A journal with an unknown action kind is refused by `undo` with a clear message; no file
      is created.
- [ ] A synthetic sort journal (MOVE and REMOVE_FOLDER entries) is undone: files back in place,
      byte-identical, mtime restored, removed source folders recreated, emptied target folders
      removed.
- [ ] A MOVE whose target was moved by hand is skipped and reported; the other entries of the
      run are still undone.
- [ ] Journals written by 0.2.0 still read, summarize and undo as before (fixture test).
- [ ] `history` shows the command of each run; documentation en + fr updated; `.po` translated.
