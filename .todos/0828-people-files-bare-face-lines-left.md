# 0828 — People files: faces still written `/data/c/…#n` beside `{path, id, face}`

- **Priority**: Low
- **Batch**: people
- **Depends**: none
- **Files**: `src/media_hygiene/config/face_refs.py`, `src/media_hygiene/services/face_refs_audit.py`, `src/media_hygiene/services/face_ids_read.py`, `src/media_hygiene/services/photo_refs_audit.py`, `src/media_hygiene/people/person_files.py`
- **Needs maintainer**: the result of the check below on the real `Maria-Angela.toml` (which folder the bare lines point to, whether it is analysed or a backup)

## Reported (maintainer, 2026-11-15)

`/config/people/Maria-Angela.toml` mixes the two forms:

```toml
{path = 'C:\Photos\2012\Mars 2012\QuartierLatin\SAM_0069.JPG', id = "34c0aa2288f319b7:4447611", face = 1},
"/data/c/Photos/iPad_Manon/IMG_0367.JPG#1",
```

"Is a mix normal?" By design it is a transition (`config/face_refs.py`, 0570): a face is
written `{path, id, face}` once its photo's id is known, else as the bare
`<container path>#<n>` of before 0570. `face_line` writes the bare form whenever the
index holds no digest for the path (naming a face on a page does not compute it), and the
end of each audit (`face_refs_audit`, 0635 `face_ids_read`) gives it its id by reading the
photo once, **except** for a photo in a backup folder (0274), not mounted, or gone. So
lines that stay bare after an audit point at one of those; the user cannot tell which,
and the file shows a container path (`/data/c/…`) a Windows reader does not know.

## What

1. Check first (measure, do not guess): on the demo tree, name a face of a photo whose
   digest the index does not hold, then `audit`: does the line become a table? Then the
   cases backup / not mounted / gone.
2. Write the id **at naming time**: the page that names a face reads the photo's digest
   once (the file is on screen, so mounted) — no bare line is written any more.
3. A bare line that stays after an audit is written with the **host path** (`C:\Photos\…`),
   never `/data/c/…`, and the audit's one line says how many faces could not be checked,
   and why (backup folder / not mounted / gone), naming the person.
4. A face whose photo is gone for good: offered for removal on `/person` (seeing first),
   never removed silently.

## Tests

- Naming a face writes `{path, id, face}` even when the index has no digest for it.
- After an audit, a face in a backup folder keeps its line, with the host path, and is
  counted in the audit's line.
- An old file with bare lines still loads (`tests/fixtures/` of 0570).
