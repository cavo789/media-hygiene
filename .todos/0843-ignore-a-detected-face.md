# 0843 — A face found by the detector can be ignored for good ("not someone to name")

- **Priority**: Medium
- **Batch**: faces
- **Depends**: none
- **Files**: `src/media_hygiene/person/forget_route.py`, `src/media_hygiene/person/templates/person.js.j2`, `src/media_hygiene/person/templates/person_names.js.j2`, `src/media_hygiene/review/templates/pick_who.js.j2`, `src/media_hygiene/review/templates/pick_who_boxes.js.j2`, `src/media_hygiene/index/`, `src/media_hygiene/faces/`, `documentation/en/commands/people.md`, `documentation/fr/commands/people.md`

## Why (maintainer, 2026-11-15)

On /person and in the large view, a face the detector found but nobody named ("? nobody")
has no ×: only named faces (`notNameButton`, "not <name>") and faces drawn by hand
(`forgetButton`, `/person/api/forget`, which refuses any face not drawn) have one. Real case: a
person's reflection in a window, detected as a face; the maintainer does not want to name it
and wants it gone, and not offered again by the next audit or face scan.

## What

- A × on every unnamed detected face, on /person's face strip and in the large view (shared
  `pick_who*`, so every large view gets it: library, browse, people), title "Not someone to
  name — ignore this face".
- Stored in the index under `/cache` (biometric data stays there), keyed so it survives a
  re-detection: by the photo's content id (`sha256[:16]:size`, as `people/*.toml`) + the face
  box, matched by overlap (the detector's boxes move slightly between runs/thresholds, 0841).
  Decide and write down what happens when the file moves (`sort`, quarantine, Explorer
  rename): the content id follows it.
- Ignored faces: not shown on the photo, not in /people groups, not counted as "to name", not
  guessed. A way back (e.g. a "faces ignored" count on the photo with "show them") so a mistake
  can be undone — seeing first, nothing silent.
- Saved then read back from the index, said on the page (never "Saved" from memory).

## Tests

- Ignore a face, re-run the face scan on the photo: it is not offered again.
- Same photo moved / renamed: still ignored.
- Undo: the face is back.
- Both languages of the docs, captures stale → `docs_screenshots` to run.
