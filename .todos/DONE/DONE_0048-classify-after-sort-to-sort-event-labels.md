# 0048 — `classify` after `sort`: a "to sort" folder named after an event label becomes a meaning

- **Priority**: Low — seen only with exact duplicates left in place (`classify` already tips to `clean` first)
- **Batch**: classify
- **Depends**: —
- **Files**: `src/media_hygiene/classify/folders.py`, `src/media_hygiene/classify/engine.py`, `tests/integration/test_sort.py`

## Context

Seen while implementing 0046, on the documentation library (`tests/support/docs/library.py`,
English) **without** running `clean`: `classify` → `sort` (no edit) → `classify` proposes to move
three files again:

```text
c/2019/To sort/Seaside holidays/IMG_0105 - Copy.jpg  sure  existing-folder  → 2019/Seaside holidays
(same for IMG_0106 - Copy.jpg and IMG_0107 - Copy.jpg)
```

The manual layout `{year}/To sort/{event}` renders `{event}` with the event's **label** (the
meaningful folder most of its files come from), not only with its span. `FolderRules.meaning()`
treats a name below "to sort" as a meaning when it is not a date: the next run reads
`Seaside holidays` as the user's folder, the files become sure and move to `2019/Seaside holidays`.
`sort` would move them again. With the demo library cleaned first (the documentation scenario),
nothing moves: the three copies are gone.

## Proposal

Decide whether a "to sort" file whose event has a label should be proposed with the label in the
first place (it may deserve `event-neighbour`, i.e. the label's folder, "to check"), or whether a
folder below "to sort" that equals the label of the file's own event keeps the file in place, as
0046 did for "to check".

## Acceptance

- [ ] On the documentation library without `clean`: `classify` → `sort` (no edit) → `classify`
      proposes nothing to move.
