# 0712 — Name one face (or a selection) on the people page, not only a whole group

- **Priority**: High
- **Batch**: people
- **Depends**: —
- **Files**: `src/media_hygiene/people/naming.py`, `src/media_hygiene/people/known.py`, `src/media_hygiene/people/templates/people_sections.js.j2`, `src/media_hygiene/people/templates/people_viewer.js.j2`, `documentation/en|fr`

Reported by the maintainer on 2026-11-11: the group "Chloé" (7,460 faces) holds faces of
her sister Manon. Today the × of a face only records "not Chloé" (`known.py`, `rejected`);
the name field names the whole group; the large view cannot name one face. So the face is
lost instead of teaching the tool who Manon is.

## Proposal

- Per face (large view, and a small menu on the tile): "Not <name>, it is… [combo]" — one
  action rules the face out of the group and gives it the typed name (existing or new
  person, same combo as the group field), saved and read back from disk.
- Per selection: the `pick_*` gestures (click, Ctrl, Shift, rectangle; skill
  `photo-picking-pages`), then "These faces are… [name]" stating the count.
- Once a person has confirmed faces, the page suggests their other faces as it already does
  (`suggest.py`), so naming a few Manon faces pulls the others out of Chloé's group.
- Tests: a face named in a named group leaves it and lands in the new person; reload keeps it.
- Docs (both languages): the people page section; `docs_screenshots` to run afterwards.
