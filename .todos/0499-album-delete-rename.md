# 0499 — Albums page: delete and rename albums

- **Priority**: High
- **Batch**: share
- **Depends**: —
- **Files**: `src/media_hygiene/share/album_store.py`, `src/media_hygiene/share/album_api.py`, `src/media_hygiene/share/templates/album.html.j2`, `src/media_hygiene/share/templates/album.js.j2`

## Why

The maintainer, 2026-10-29: "Comment pourrais-je faire pour supprimer un album ? Via l'interface
bien sûr. Je ne vois aucune page qui me donne la liste des albums et que je pourrais cocher pour
suppression. Et si je voulais éditer un album ? Voir les photos qu'il contient et en supprimer et,
aussi, ajouter des photos ?" Today `/albums` (0297) lists the albums and opens one; a photo is
taken out one at a time from the large view, added to another album, or made the cover. An
album only disappears when its last photo is taken out.

## What

- On the list of `/albums` (PC only; the phone stays read-only, 0435): a tick per album and
  **🗑 Delete** for the albums ticked, and **✏️ Rename** on an album.
- Delete: asks once in the page ("Delete 2 albums? Your photos stay where they are: only the
  albums file changes."), then `AlbumAsked` action `delete` (`album_store.delete`); the answer is
  read back from the disk and shown (product rule). Offer **Undo** in the message: the deleted
  albums kept in memory by the page and re-added (or a `albums.json` backup next to it: choose,
  say it in the feedback).
- Rename: action `rename` + `to`; refused when the new name is another album's (case-insensitive,
  `same_name`), or not a valid name (`_new_album` rules). `mh slideshow/share/album --album` take
  the new name at once.
- The folder of links made by `mh album` (0462) keeps the old name: say so in the message, or
  rename it too — check what 0462 built first.
- Tests: delete, delete several, rename, rename onto an existing name refused, phone refused.
- Docs (en + fr): `commands/` page of the albums page / share chapter.
