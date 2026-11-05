# 0596 — Sort here now and Move to an event ignore the target and the layout chosen

- **Priority**: Medium
- **Batch**: one-interface
- **Depends**: 0533 (DONE)
- **Files**: `src/media_hygiene/services/selection_move.py`, `src/media_hygiene/services/group_sort.py`, `documentation/en/commands/search.md`, `documentation/fr/commands/search.md`
- **Needs maintainer**: a decision (below)

## Found (0533)

`SelectionMover` hard-codes `YYYY/YYYY-MM/<name>` below the root of the photos; `[classify] target`
and `layout`, now chosen on the same tab, only drive `classify`/`sort`. The page says so.

## Question for the maintainer

Should those two buttons honour the target (and *Year / Month only*, an event then having no
folder)? Proposed: the target yes; the event's folder kept, since the user named it.
