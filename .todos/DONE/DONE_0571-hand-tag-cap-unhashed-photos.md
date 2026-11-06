# 0571 — 🏷 Tag…: a fixed cap on photos not hashed yet

- **Priority**: Low
- **Batch**: search
- **Depends**: —
- **Files**: `src/media_hygiene/search/tag_desk.py`, `src/media_hygiene/tags/hand_edit.py`, `src/media_hygiene/search/templates/hand_tag.js.j2`, `documentation/en/commands/search.md`, `documentation/fr/commands/search.md`

## Why

0555 **tags tapés à la main sur une sélection**: a photo whose content id is not in the index yet
is hashed from disk while the page waits, with no limit. With 2 000 such photos the page waits
for minutes. The maintainer decided on 2026-11-02: a fixed cap (a constant, not a setting) and a
message.

## What

- More than ~200 picked photos not hashed yet: nothing is saved, and the dialog says in one line
  « N photos not analysed yet: run an audit first » (`_()`, fr).
- Test: under the cap saves, over it refuses with nothing written.
