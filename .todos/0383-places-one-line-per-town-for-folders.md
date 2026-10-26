# 0383 — places: the folders of one town merged into one line, one pin

- **Priority**: Medium
- **Batch**: places
- **Depends**: —
- **Files**: `src/media_hygiene/places/folder_rows.py`, `src/media_hygiene/places/folders.py`, `src/media_hygiene/places/config_folders.py`, `src/media_hygiene/places/app.py`, `src/media_hygiene/places/templates/places.html.j2`, `documentation/en/commands/places.md`, `documentation/fr/commands/places.md`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`

## Why

The folders list of the map page (`mh places`, the **Placed** part) shows one line per folder
(`folder_rows`: one `FolderRow` per host path, a `[[places.folders]]` entry per folder). A
collection sorted by year holds the same town many times (`2019\Paris`, `2023\Paris`…), so the
list repeats it. Seen on the maintainer's collection (screenshot, 2026-10-25):

- Paris — 33 photos, Paris — 8 photos
- Quimper — 10 photos, Quimper — 28 photos
- Strasbourg — 610 photos, Strasbourg — 75 photos, 1 video
- Turin — 41, 80 and 5 photos

Each line is opened, its pin dragged and saved on its own: the same work two or three times, and
the pins of one town end up a few hundred metres apart for no reason. The maintainer wants **one
place per town**.

## What to do

1. **One line per town** in both parts of the list (**To place** and **Placed**): the folders
   whose `town` is the same (`geo.folding.town_key` + country, so `Turin`/`turin` meet) become one
   line, `📌 Turin — 126 photos without GPS · 3 folders`, the counts summed. A folder without a
   town (placed by hand, shown by its last folder name) stays alone: its name is no proof.
   The ▸ of the line unfolds its folders (host path, count), each still openable alone, as today.
2. **One pin for the group**: opening the line shows every photo of its folders in the drawer
   (`GET /api/folder/` gets a group form, or a new route — to decide while coding) and one pin;
   **Save** writes that position for every folder of the group, in one atomic write of
   `config.toml` (`toml_edit`), read back before the page says so (product rule).
3. **Folders saved at different spots**: the group line marks it (e.g. `📌 Turin — … · 3 positions`)
   and its pin starts at the position of the folder with the most photos; one Save aligns them.
   Opening one folder from the unfolded list and saving it alone stays possible (a town big enough
   for two real spots: Paris airport vs the city).
4. **Forget** on the group forgets every folder of it; on one folder, that folder only.
5. A saved folder not found (⚠, renamed or moved) stays a line of its own at the top, as now: it
   cannot join a group whose folders exist without hiding the warning.

## Storage — keep one entry per folder

`[[places.folders]]` keeps one `{folder, latitude, longitude}` per folder; the group is a view,
computed from the town names at each read. Alternatives set aside:

- a `folders = [...]` list per entry: one rename in Explorer would leave a group half found, and
  `xmp`, `classify` (`folder_town`) and `sort`'s path rewrite (0382) read one folder per entry
  today — all of them would change for a display need;
- a `[[classify.places]]` circle named after the town: it would also capture photos **with** GPS
  in that circle, which is another feature.

So nothing changes for `xmp` / `classify` / `sort`; only the page and the save route learn about
groups.

## Tests

- `folder_rows`/grouping: three folders named `Turin` (two saved at different points, one not
  saved) → one group, 3 folders, counts summed, `positions: 2`; a folder placed by hand without a
  town stays alone; a ⚠ missing folder stays alone; `Turin` vs `turin` → one group; one town
  name in two countries (two `Paris` of the gazetteer, FR and US) → two groups.
- Save route, group form: every folder of the group written once, comments of `config.toml`
  kept, the answer read back from disk; forget on the group removes all of them, not the others.
- The page: the template test that checks the list's strings (`_()` in the `T` table).

## Done when

- The maintainer's list shows one Paris, one Quimper, one Strasbourg, one Turin line; one Save
  places all of a town's folders.
- Both languages of `commands/places.md` say it; `i18n_update` + French translation; say that
  `docs_screenshots` should run (the places page changes).
