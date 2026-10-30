# 0540 — A step proven done is turned off, its reason in plain words (clean, sort)

- **Priority**: High — the page invites a click that can only answer "nothing to do"
- **Batch**: home
- **Depends**: —
- **Files**: `src/media_hygiene/cli/menu_needs.py`, `src/media_hygiene/cli/menu_steps.py`, `src/media_hygiene/cli/menu_catalog_sort.py`, `src/media_hygiene/cli/cmd_clean.py`, `src/media_hygiene/services/status_parts.py`, `src/media_hygiene/review/templates/home_draw.js.j2`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/`, `documentation/fr/`, `tests/unit/test_menu_*.py`

## Asked (maintainer, 2026-10-30)

"In /#clean, *Set the extra copies aside*: I ran it and the console said ✅ *Nothing to clean: no
duplicate and no broken file.* Since the page already shows ✅ instead of the step number, you
knew it was useless: why not disable it? You do it in /#sort for step 4 *Move the photos as the
workbook says* (an odd name: 'as the workbook says'?). And I never used the workbook: how can
that step be off because 'Already sorted'?"

## What the code does today (read 2026-10-30)

Two separate rules, which do not agree:

- `menu_steps._done()` decides the ✅ (`st.done` in `home_draw.js.j2`, `_DONE` in `mh menu`).
  `Slot.CLEAN` is done when the last summary is a clean run **or** has no duplicate file.
- `menu_needs.missing()` decides the button off and the reason shown instead. It has a rule for
  `sort` (`_proposal`) and none for `clean`. So clean shows ✅ but stays clickable. Sort is off with
  *Already sorted as the workbook says.*
- `cmd_clean.py:109` tests something else again: *no duplicate and no broken file*. `_done` ignores
  broken files, so the ✅ and the console can disagree both ways.
- `sort_state()`: `sorted` is True when the newest sort run not undone **started after the newest
  `plan.json`'s mtime**. The "workbook" (`classify.xlsx`) is just how the classify proposal is
  shown. Any `classify` run from the page (*Propose a layout*), then any `sort`, counts as "sorted
  as the workbook says", even if the user never opened Excel. A sort run that moved nothing, or
  one from an older test, also counts. To check on the maintainer's tool folders: which
  `plan.json` and which sort run made it True (`/reports/*/plan.json`, `mh history`).

## What

1. **One rule for "nothing to do"**, shared by the ✅, the off button and the command itself.
   Clean gets a `missing()` rule: off when the last audit found no duplicate and no broken file,
   using the same test as `cmd_clean` (move it into one function both call, so they cannot
   drift). Its reason must say that it depends on the last audit:
   *Nothing to set aside since the audit of {date}: audit again after adding photos.* A ✅ step
   that can still run is a bug; a test walks every slot: done ⇒ `missing()` is not None, or the
   step is on the documented list of repeatable steps (audit, tags…).
2. **The sort step, renamed for what it does**: *Move the photos into the proposed folders*
   (FR: *Ranger les photos dans les dossiers proposés*), with a description saying the
   proposal can be changed first, on the page or in the workbook (the fast path of 0524). The
   word "workbook" stays out of the label: most users never open it.
3. **Its reason, from what really happened**, never from a file the user did not touch: *Already
   done: the proposal of {date} was applied on {date} ({n} files moved).* With 0 files moved, or
   none of the proposal's files moved, it is not "sorted": say *Nothing left to move in the
   proposal of {date}*, or leave the step on. Add the run's moved count to `SortState`
   (from the journal, `journal` field, 0398).
4. Same review for every other step with a ✅ (`CLASSIFY`, `TAGS`, `PEOPLE`): does the reason say
   what proves it, in the user's words, with a date?
5. Docs EN + FR: the sort step's new name everywhere it is quoted (`sort/` guide, `commands/sort.md`,
   quick guides); `docs_screenshots` to run afterwards (home and menu captures change).

## Done when

- On the maintainer's state of 2026-10-30, /#clean shows *Set the extra copies aside* off, with
  the reason and the audit date in its place; clicking it is impossible. `mh menu` shows it
  unnumbered with the same reason.
- `mh menu` and the home page show the same off steps with the same reasons (one function).
- The sort step's label does not say "workbook"; its reason names the dates and the files moved,
  and is not shown after a sort that moved nothing.
- The test of item 1 passes for every slot; i18n complete; docs EN/FR in parity.
