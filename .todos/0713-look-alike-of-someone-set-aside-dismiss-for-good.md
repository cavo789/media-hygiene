# 0713 — Look-alikes of a person set aside: "Not them" saved, clearer wording

- **Priority**: High
- **Batch**: people
- **Depends**: —
- **Files**: `src/media_hygiene/people/alike.py`, `src/media_hygiene/people/remembered.py`, `src/media_hygiene/people/aside.py`, `src/media_hygiene/people/templates/people_sections.js.j2`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`

Reported by the maintainer on 2026-11-11: the blocks "n other photos look like the person
you set aside on <date>" (`alike.py`, LOOK_ALIKE 0.40) showed their own daughters next to an
ex-boyfriend set aside. The × only lives in the page's memory (`outAlike` in JS): after a
reload the same faces come back. There is no "ignore this block", and "Mettre de côté" did
not say it means removing the photos (quarantine, undoable), so the maintainer did not dare
click.

## Proposal

- The × of a look-alike face is saved (cache, beside `remembered` — "face X is not aside
  person P"), read back from disk; `alike.py` skips those faces for that person.
- A button "Not them — ignore these n" per block: saves every face shown (count stated,
  never hidden ones) as not that person; the block disappears for good; undo possible
  (↺ list or a "show ignored" toggle).
- Wording: the main button says what happens — e.g. "Remove these 2 photos too (quarantine,
  undo possible)" — and the hint explains set aside = removed at the next clean.
- Tests: × and "ignore" survive a reload; an ignored face never reappears for that person
  but still can for another one set aside; taking the person back forgets the ignores.
- `i18n_update` + French; docs both languages; `docs_screenshots` to run afterwards.
- Report: should LOOK_ALIKE (0.40) become a setting? Measure first how many false alikes the
  maintainer's collection gives.
