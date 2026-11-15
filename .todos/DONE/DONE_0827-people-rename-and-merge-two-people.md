# 0827 — People: rename a person, merge two people (a typo made two files)

- **Priority**: Medium
- **Batch**: people
- **Depends**: none
- **Files**: `src/media_hygiene/people/roster.py`, `src/media_hygiene/people/config_file.py`, `src/media_hygiene/people/person_files.py`, `src/media_hygiene/people/templates/`, `src/media_hygiene/person/templates/person_names.js.j2`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/commands/people.md`, `documentation/fr/commands/people.md`
- **Needs maintainer**: try it on the real `Maria-Angelaela` → `Maria-Angela` case (left on the PC on purpose)

## Reported (maintainer, 2026-11-15)

The 🚫 *Avoid some people* list of the slideshow shows both `Maria-Angela` and
`Maria-Angelaela`: a typo when naming made a second person, with its own file
`/config/people/Maria-Angelaela.toml` next to the right `Maria-Angela.toml`. Nothing in
the pages fixes it today: the user would have to edit `config.toml` and both files by hand.

## What

- On `/people` (and wherever a person's name is shown with its faces: `/person`'s naming
  line, same shared part), **Rename** a person. A new name that is **already a person's**
  turns the rename into a **merge**, said before it runs: "Maria-Angelaela (12 faces) joins
  Maria-Angela (340 faces): 3 faces in both are kept once."
- Merge = `faces` of both, each face once (same `id` + `face`, or same container path +
  face for the forms before 0570); `rejected` of both, once; a face **named by one and
  rejected by the other** is a conflict: shown with its photo, the user picks (seeing
  first; never settled silently). Then `config.toml` links one file only, the other file
  is removed (`person_files` already removes files nobody links), both kept first in
  `/config/.history/` (`file_history.replace_text`).
- Save proven: read back from disk, the page shows the person's count after the merge.
- Everything that names people by name follows: albums of a person, `[[classify.rules]]`
  or tags naming them, `people/ignored.toml` untouched. List them before coding
  (grep the readers of `[people]`); what cannot follow is said in the confirmation.
- Phone/TV: read-only, no Rename there.

## Tests

- Rename to a free name: one file renamed, `config.toml` updated, faces intact.
- Merge with duplicates: each face once; rejected merged; the other file gone, both in
  `.history`.
- Named in one, rejected in the other: the merge waits for the user's choice.
- Names differing by case only (`maria-angela`) merge, as `person_files` never lets them
  share a file.
