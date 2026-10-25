# 0387 — review-sort: one Dossier field, one line says where the files go and if it is saved

- **Priority**: High
- **Batch**: review-sort
- **Depends**: 0385
- **Files**: `src/media_hygiene/review/templates/sort_review.html.j2`, `src/media_hygiene/review/sort_views.py`, `src/media_hygiene/review/sort_app.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/commands/review-sort.md`, `documentation/fr/commands/review-sort.md`, `documentation/en/sort/11-name-events-in-the-browser.md`, `documentation/fr/sort/11-name-events-in-the-browser.md`

## Why

The maintainer on the page, 2026-10-25, "completely lost":

- The name field shows "Photos Chloé" in grey (the event's label, a placeholder) and the category
  field "Photos Chloé" again (the proposal, prefilled): "why twice? what is a category here?".
- Typing "Vacances au Monténégro" changes nothing visible: **Proposé** is classify's opinion and
  never moves, and with `{year}/{category}` a filled category makes the name ignored
  (`_by_event`: `category = event.category or event.name …`) — measured with `resolve()`, see 0385.
- "Is the category a sub-folder (`2019/Vacances au Monténégro/Budva`)?" — nothing on the page
  answers it.

- "Chosen here: nothing" (maintainer, 2026-10-25: "I don't know what this line is for — for
  nothing at all"): it fills only after Enter. And what is typed without Enter is **lost
  silently** when moving to another event (N, P, U): read in `sort_review.html.j2`, the fields are
  refilled from the card (lines 187-190), no unsaved-change check.

## What

Decided by the maintainer, 2026-10-25: **one field, Dossier**, replaces Name + Category.

- **Dossier**: `2011/` shown fixed (the year of the layout), then one wide field holding the path
  under it, prefilled with the proposal (`Fêtes/Communions/Communion de Manon 2011`), completed
  from the folders already used. Wide enough for such paths (the current category field cuts
  them, screenshot of 2026-10-25).
- The event's **name** (albums, carried over by `classify`) is the last segment of that path by
  default; changeable in a folded "Name of the event" option. Nothing else to type.
- Recorded as today's event edit (category = the path, name = the name) so the workbook, `sort`
  and the carry-over keep working; the user's own folders stay under it (0385).
- A **Destination** line under the field, computed as `sort` will (`resolve` on the plan + the
  value being typed, server side): "→ 212 files go to C:\Photos\2011\Fêtes\Communions\
  Communion de Manon 2011 · 40 keep their own folder below it", updated as the user types.
- The `{year}/{category}/{event}` question is settled by this: no layout change needed.
- Left column: **Proposed**, **Workbook** and **Chosen here** become **one state line** of the
  destination: "proposed by classify, not validated yet" · "changed, not saved yet: Enter" ·
  "validated here at 14:32" (read back from `sort-decisions.json`) · the workbook's value only
  when it says something else (a conflict in red).
- Typed but not saved: N, P, U and closing the tab do not drop it silently — Enter saves, Esc
  drops, moving away asks (or saves: to decide while implementing, say which in the feedback).

## Tests

The destination endpoint against `resolve` (same folder); a typed name over a proposed
category; the page's text in both languages. Say that `docs_screenshots` should run.
