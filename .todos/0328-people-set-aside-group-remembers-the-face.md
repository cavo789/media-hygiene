# 0328 — People page: a group set aside remembers its face, and finds the photos it missed

- **Priority**: High
- **Batch**: people
- **Depends**: 0327
- **Files**: `src/media_hygiene/people/aside.py`, `src/media_hygiene/people/sections.py`, `src/media_hygiene/people/views.py`, `src/media_hygiene/people/templates/people.html.j2`, `src/media_hygiene/index/face_schema.py`, `src/media_hygiene/index/face_rows.py`, `src/media_hygiene/index/parked.py`, `src/media_hygiene/faces/similarity.py`, `tests/integration/people/test_people_aside.py`, `documentation/en/commands/people.md`, `documentation/fr/commands/people.md`

## Why

The maintainer, 2026-10-23: they set aside the photos of an unnamed group on `mh people` (a
person they never want to see again, no name given) — 140 photos applied to the quarantine
that day at 12:23 (read-only check of `/reports/decisions.applied-20261023-122322.json`). One
photo of that person escaped: on the page, in another section, a face in profile next to
someone else. They want "this person, I never want to see again" to hold, without naming them.

Today "Set aside their n photos" is one shot: it writes paths into the decisions file
(`people/aside.py`) and forgets which face it was about. Once `clean` moves the photos, their
face rows are parked (`index/parked.py`) and dropped by `purge`: nothing is left to compare the
next photos with.

## What

- **Setting a group aside remembers its face, anonymously**: the face vectors of the faces sent
  (those not taken out by ×) are kept in the cache, in a table of their own (`set_aside_faces`:
  vector, a set-aside id, date, label), not keyed by path — the photos move to the quarantine,
  then are erased by `purge`, the vectors must survive both. No name, nothing in `/config`
  (`config.toml` never holds a face vector). Taking the photos back (`Take back`, `undo`)
  forgets that face.
- **Faces that look like it are shown, never removed silently**: after the set aside, and at
  each later opening of the page, the faces still in the cache coming close to a remembered
  face — with a looser threshold than `[people] similarity`, and including the faces left out
  of the groups (smaller than `min_face`, blurrier than `min_sharpness`, alone) — form a section
  at the top: "n other photos look like the person you set aside on <date>", with "Set them
  aside too" and × per face. A new photo added later shows there on the next page opening
  (decided 2026-10-23: shown to check, not set aside automatically).
- Threshold: to measure on synthetic faces (and on the maintainer's set aside, read-only: did
  the escaped profile face come close?), not guessed; propose `[people] set_aside_similarity`.
- A face never detected (strong profile) cannot be found this way: 0329 covers it (one photo
  set aside by hand).
- What happens when files move: the remembered vectors carry no path; the faces compared are
  the cache's current ones (`sort`, `undo`, a folder renamed: the index follows its rows).

## Decided (2026-10-24)

By the maintainer, during `/todo:iterate`: **yes**, the faces stored for the photos set aside on
2026-10-23 (still in the index until `mh purge`) may be read, **read-only**, to choose the
threshold. How (as before, memory *Local photos and Ollama*): the host Docker volume
`media-hygiene-cache` mounted `readonly` into a throwaway container, SQLite opened with
`?mode=ro&immutable=1`; nothing written, no copy of a face or a path into the repository; the
figures only (distances of the escaped faces to the set-aside group, measured) go into the
TODO's outcome and the private feedback file. If the volume is not reachable from the
devcontainer, a read-only step in `tests/measure/mh-measure.ps1` instead.

No new setting for the threshold unless the measure shows it must vary between collections
(the maintainer, 2026-10-24: "à force de créer des réglages, on va en avoir des centaines"):
a constant, named and explained, is the default choice.

## Tests

- Integration: set aside a group → its vectors are stored; a close face elsewhere shows in the
  "look like" section, a far one does not; `Take back` forgets the face; `clean` + `purge` keep
  the vectors.
- Docs en + fr; captures stale → `docs_screenshots`.
