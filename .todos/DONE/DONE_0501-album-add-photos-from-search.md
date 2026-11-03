# 0501 — Albums page: Add photos opens search aimed at the album

- **Priority**: Medium
- **Batch**: share
- **Depends**: —
- **Files**: `src/media_hygiene/share/templates/album.js.j2`, `src/media_hygiene/review/templates/album_bar.html.j2`, `src/media_hygiene/search/templates/search.js.j2`, `src/media_hygiene/services/search_app.py`

## Why

The maintainer, 2026-10-29: "Comment pourrais-je faire pour supprimer un album ? Via l'interface
bien sûr. Je ne vois aucune page qui me donne la liste des albums et que je pourrais cocher pour
suppression. Et si je voulais éditer un album ? Voir les photos qu'il contient et en supprimer et,
aussi, ajouter des photos ?" Today `/albums` (0297) lists the albums and opens one; a photo is
taken out one at a time from the large view, added to another album, or made the cover. An
album only disappears when its last photo is taken out.

## What

- An album opened on `/albums` offers **➕ Add photos**: it opens search (served by the home
  server, same tab) with the album named in the album field (`?album=<name>` read once by
  `album_bar.html.j2`; not remembered afterwards, see 2026-10-29: the field starts empty), the
  search period around the album's dates, and a way back to the album.
- In search, a filter **In the album / Not in the album** (the album named): the photos already in
  it are marked on their tile, so adding twice is visible (adding is already idempotent).
- Tests: the field filled from the address, the filter, the way back.
