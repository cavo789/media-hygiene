# 0317 — `search`: a × on a person's name under a photo takes the name off (rejected), without leaving the page

- **Priority**: Medium
- **Batch**: people
- **Depends**: 0316
- **Files**: `src/media_hygiene/search/people_words.py`, `src/media_hygiene/search/hits.py`, `src/media_hygiene/search/app.py`, `src/media_hygiene/search/templates/search.js.j2`, `src/media_hygiene/search/templates/browse.js.j2`, `src/media_hygiene/people/changes.py`, `src/media_hygiene/people/config_file.py`, `src/media_hygiene/people/proof.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/commands/search.md`, `documentation/fr/commands/search.md`, `tests/integration/test_search_people_reject.py`

## Why

The maintainer, 2026-10-23, after seeing "Marie Saive" under two photos where she is not
(`IMG_20180517_203027.jpg`: the man in profile was assigned her name at 0.413; `HNI_0099.JPG`,
see 0316): "could the tags under the photos be clickable, with a small cross? Clicking it on
'Marie Saive' in `mh search` would remove that association, so the photo goes into the person's
`rejected` list. Then I can manage this without leaving Search."

Today the only fix is on the people page (× in "Marie Saive attribué"), which means finding the
face again among thousands. A user of `mh` cannot ask Claude which face it was.

## What

- `people_words` keeps, per photo and per name, **which faces** gave the name
  (`<path>#<n>` ids; a photo may have two faces assigned the same person). They stay in memory,
  as now, and are sent to the page with the hit (only for `person` tags).
- The search card shows a × on each `person` chip, never on other tags (folder words, dates and
  places are not wrong in the same way). Clicking the × does **not** pick the card: stop the
  event so the grid's gestures stay intact (skill `photo-picking-pages`). The large view's facts
  panel (`I`) shows the same chips with the same ×.
- `POST /api/people/reject` (JSON only, loopback `Host`, as the other routes): body
  `{name, faces}`. It reuses `people/changes.reject_faces` and `save_people`, the same path as
  the people page, so the result is identical: assigned faces go into `rejected`, and a
  **confirmed** face is also taken out of `faces` (to check: what `reject_faces` already does
  with a confirmed face). Then it reads `config.toml` and the person file back from disk and
  answers with `proof_line`.
- The page shows that line, removes the chip and keeps the card in place (`relabel`, no
  re-search). Other photos named only because they are close to the rejected face are not
  touched; they keep their name until rejected or until 0318 shows why.
- Undo: the line offers *Put back* (removes the ids from `rejected`; a confirmed face
  taken out goes back to `faces`), saved and read back the same way.
- `classify`, inventory and XMP see the change at their next run (names are computed per run).

## Tests

- Reject an assigned name: the face id is in `rejected` of `people/<name>.toml`, read back, and
  `people_words` no longer gives that name for the photo.
- Reject on a photo with two faces assigned the same person: both ids go into `rejected`.
- Reject a confirmed face: out of `faces`, into `rejected`.
- *Put back* restores the file exactly (byte compare of the person file).
- A non-JSON `POST` or a foreign `Host` is refused.
- Headless check (skill `photo-picking-pages`, checklist 2): a click on × does not pick the
  card; the grid's top does not move.

## Docs

`commands/search.md` (both languages): the × on a name, what it writes and where, *Put back*.
Say that `docs_screenshots` should run.
