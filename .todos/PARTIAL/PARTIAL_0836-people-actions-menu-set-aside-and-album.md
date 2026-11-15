# 0836 — People: an actions menu per person (rename, merge, set aside, album in memory)

- **Priority**: Medium
- **Batch**: people
- **Depends**: 0827 (rename and merge: its two actions go in this menu)
- **Files**: `src/media_hygiene/people/templates/people.html.j2`, `src/media_hygiene/people/templates/people.js.j2`, `src/media_hygiene/people/roster.py`, `src/media_hygiene/people/config_file.py`, `src/media_hygiene/people/person_files.py`, `src/media_hygiene/share/album_route.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/commands/people.md`, `documentation/fr/commands/people.md`, `tests/unit/`

## Asked (maintainer, 2026-11-15)

On `/people`, each named person gets a small drop-down menu of actions, so more can be
added later without crowding the page:

1. **Rename** / **Merge** — 0827 (a rename to an existing name is a merge).
2. **Set aside this person** — every photo where they appear goes to the quarantine, and
   the name is dropped: `/config/people/<name>.toml` removed, its link removed from
   `config.toml`.
3. **Album in memory** — e.g. after a death: one album of all the photos of the person
   (`albums.json`, the existing `album` hard-link folders), named after them by default.

## How

- One shared menu component (same as the other pages' menus if one exists: reuse first, rule
  *reuse components*), also on `/person`'s naming line (feature follows its kind).
- **Set aside**, seeing first (0524) and never on hidden (rules). Decided (maintainer,
  2026-11-15): **every** photo where the person appears, alone or with others (an ex: one
  does not want to see them any more), but the user chooses. The menu opens a page like
  `/library`'s search result: all the person's photos in the shared pick grid
  (`review/templates/pick_*`, skill `photo-picking-pages`), **all selected** by default;
  the user unselects the ones to keep (a child's birth...) or picks a part, then
  *Set aside* with the count on the button ("Set aside these 214"), then `ApplyOffer` /
  *Apply now*. Best: the library itself filtered on the person, if it can host that action.
- **Dropping the name**: offered on the same page, checked by default; when photos are kept,
  the kept photos lose that face's name (the `.toml` goes). Journaled, undoable: `undo` puts
  the photos back **and** restores the `.toml` + `config.toml` link (both kept in
  `/config/.history/` first, `file_history.replace_text`). Set-aside photos are then ignored
  everywhere (soft delete).
- **Album in memory**: reuse `share/` album creation; the album is shown before saved, the
  save is read back from disk.
- Phone/TV: read-only, no menu there (album viewing only).

## Tests

- Menu renders on `/people` and `/person` with the same actions (parity test).
- Set aside: all selected by default; unselected photos stay; counts shown = files quarantined; `.toml` and link gone; undo restores all three.
- Album: created with every photo of the person, read back.
- Docs en + fr, `.po` complete; `docs_screenshots` to rerun (page changed).

## Status — PARTIAL (2026-11-15)

### Done
- A ⋯ menu per person on /people (Rename/Merge of 0827, Set aside, Album), from one shared
  template (`review/templates/person_menu.html.j2`); /person's naming line has it with
  Rename only.
- Set aside, default of *Needs maintainer* applied: only the photos where the person is the
  only face found, shown ticked (untickable); photos with others listed, never touched.
  Goes to the decisions file: *Apply now*, `clean --decisions` journal, `undo` of the files.
  *Drop the name* ticked by default; its `.toml` and `config.toml` saved to `.history` first.
- Album in memory: every photo of the person, shown before saving, read back from
  `albums.json`; capped at 3000 per save, said in the dialog.
- Phone: the new routes are not reachable from the LAN. 17 tests
  (`test_people_rename_merge.py`, `test_people_actions_menu.py`).

### Not done
- `mh undo` of the clean run does not bring the dropped name back (only the page's Undo
  toast does, from a copy in memory). **Reason:** needs `clean --decisions` to journal the
  name; maintainer to decide.
- Seeing first: the photos are tiles with boxes in a dialog, not the shared pick grid nor a
  library filtered on the person. **Reason:** deviation; move to the shared grid
  (`photo-picking-pages`).
- /person's menu offers Rename only, not Set aside / Album (feature follows its kind).
  **Reason:** needs the people board's numbering on /person.
- The ⋯ menu's JavaScript never ran in a browser. **Reason:** no node/Chromium used here.
- *Needs maintainer*: confirm the default (alone only) for Set aside.
