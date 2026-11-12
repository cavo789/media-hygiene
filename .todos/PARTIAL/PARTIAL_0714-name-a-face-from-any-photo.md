# 0714 — Name a face from any photo, then confirm that person's other photos

- **Priority**: High
- **Batch**: people
- **Depends**: 0712
- **Files**: `src/media_hygiene/person/app.py`, `src/media_hygiene/person/finding.py`, `src/media_hygiene/person/templates/person.html.j2`, `src/media_hygiene/person/templates/person.js.j2`, `src/media_hygiene/people/known.py`, `src/media_hygiene/people/naming.py`, `src/media_hygiene/review/templates/pick_viewer.html.j2`, `src/media_hygiene/cli/menu_catalog_find.py`, `documentation/en|fr/commands/people.md`, `documentation/en|fr/commands/library.md`

Asked by the maintainer on 2026-11-12: after going through the people page, photos still show
people the tool never asked about ("this is Aunt Juliette"). Today `/person` (0351) shows the
faces of one photo and that face's other photos, but only to set them aside; naming happens
only on the people page, on whole groups (0712: one face, still from a group). A person whose
faces sit in a small group far down the page, or inside someone else's group, is never named.

The maintainer did not know `/person` existed: it is reached only from the 👤 of the large
view (`pick_viewer`) and of `review`, labelled "set a person aside". Part of this TODO is to
make it findable.

## Proposal

1. **Who is this?** — the 👤 of the large view (every tile page) and of `review` opens
   `/person` on the photo, renamed from "set a person aside" (it frightens: the maintainer feared clicking it) to "👤 Identify someone" (FR "Identifier quelqu'un") (both
   uses: name, set aside). Also an entry in the home page and `mh menu`
   (`menu_catalog_find.py`): "Name someone from a photo", the page with its path field.
2. **Name the face** — on `/person`, each detected face gets "This is… [combo]", the same
   combo as the people page group field (existing person or a new one; shared with 0712).
   Saved in `/config/people/<name>.toml` as a confirmed face (`known.py`), read back from
   disk and shown.
3. **See first, then confirm** — right after naming, the grid shows that face's photos
   (`likeness`, closest first), picked with the `pick_*` gestures (skill
   `photo-picking-pages`); "These are <name>: 37" confirms the selection, stating its count.
   Hidden or unchecked tiles stay undecided. A face already named elsewhere says so on its
   tile ("Chloé") so a click does not silently move it; moving it is the 0712 action.
4. **Feed the people page** — the confirmed faces make the person appear on the people page,
   and `suggest.py` attributes her other groups as for any confirmed face (nothing new to
   compute).

5. **Who is on this photo, at a glance** — asked on 2026-11-12 from the `library` large
   view: today no page says whether the faces of a photo were detected nor whom they were
   given to; `/person` shows the faces without their names. Show, under the large view
   (every tile page, `review`), one line "👤 Chloé · ? (not named) · 1 face too small" from
   the index, and the same name (or "?") on each face of `/person`, the ones confirmed told
   apart from the ones only attributed by the tool. Clicking a "?" opens step 2 on that face.

6. **Say "not him" on a wrong photo** — measured 2026-11-12 on `/person` from
   `IMG_8634.JPG`: 53 photos found for one face, several without that person at all.
   `/person` finds by likeness only (`person/likeness.py`: the faces close to the clicked
   face, their mean, two rounds; `LOOK_ALIKE`), never by name, and a tile shows the whole
   photo, not which face matched. Each tile then shows the matched face (a small crop, or
   its box on the large view) and, once the face is named, a name tag with a ×: the × records
   "not <name>" for that face (`known.py`, `rejected`, as the people page does), reads it
   back, removes the tile, and the mean is recomputed without it. Before the face is
   named, the × only drops the tile from this search.

Out of scope: a face the detector missed (0715).

## Tests

- Naming a face on `/person` writes it to the person file; reload shows it named.
- A new name creates the person; an existing name adds to it.
- Confirming a selection of N photos records exactly those N faces; hidden tiles untouched.
- A face already named someone else is shown with that name and is not renamed by a
  selection unless explicitly moved.
- The large view line lists each face of a photo with its name, attributed, or "?".
- A × on a tile records "not <name>" for the matched face; reload: tile gone, face rejected.
- The people page then lists the person with the confirmed faces.

## Docs

Both languages: `commands/people.md` (the "from any page" section becomes "name or set
aside someone from any photo"), `library.md` and `review.md` (the 👤 label), the menu entry.
`docs_screenshots` to run afterwards.
