# 0330 — "Make room on the phone": filed under Clean, still step 2 of "From a phone"

- **Priority**: Medium
- **Batch**: menu
- **Depends**: —
- **Files**: `src/media_hygiene/cli/menu_catalog_import.py`, `src/media_hygiene/cli/menu_catalog_clean.py`, `tests/unit/test_menu_catalog.py`

## Why

The maintainer, 2026-10-23, on the home page: under *Import photos* → *From a phone*, step 1
*Copy the new photos of the phone* then step 2 *Make room on the phone* reads naturally (copy,
then free). But *Make room on the phone* deletes for good (⚠️ `Risk.FINAL`): by its kind, it
belongs to *Clean up*. Both logics must hold, the sequence and the category.

The catalog already shows one action in several spaces: a `Step` has one home `space` (the
palette, Ctrl+K, names it beside the action: `home_run.js.j2`, `action.space`), and any
`Group` of any `Area` may list it. Seven actions do so today, measured with the catalog
(2026-10-23): `open`, `history`, `undo`, `purge` (home *History*/*Reports*, shown in the clean
guide), `import`, `nas-add`, `folders-add`.

## What

Approved by the maintainer, 2026-10-23:

1. `phone-free`'s home space becomes `Space.CLEAN` (`menu_catalog_import.py`): the palette files
   it under *Clean up*.
2. It stays step 2 of the numbered group *From a phone* in the import area (unchanged).
3. `clean_area()` (`menu_catalog_clean.py`) lists it in *Go further*, next to `shrink` (the other
   action that makes room).

Not in the numbered clean guide: that guide is about the PC's duplicates, and the action is
optional (`optional=True`).

Check that a step listed in two areas keeps one entry in the palette (no duplicate result)
and that its number in *From a phone* is unchanged (`menu_view.py` numbers per group).

## Tests

`test_menu_catalog.py`: `phone-free` has `Space.CLEAN` as its home, is listed both in the
import area's *From a phone* (second) and in the clean area's *Go further*.

## Docs

The home page changes: say that `docs_screenshots` should run (not unasked). The reference of
the menu, if a page lists the actions per space, in both languages.

## Explicit NON-goals

- The confirmation dialog of `phone-free` (0311).
- Moving the step's code (`Step(...)` stays in `import_steps()`, near its step 1).
