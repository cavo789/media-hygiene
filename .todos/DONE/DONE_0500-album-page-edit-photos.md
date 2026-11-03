# 0500 — Albums page: an album as a grid of tiles to pick and take out

- **Priority**: High
- **Batch**: share
- **Depends**: —
- **Files**: `src/media_hygiene/share/templates/album.html.j2`, `src/media_hygiene/share/templates/album.js.j2`, `src/media_hygiene/services/album_pages.py`, `src/media_hygiene/review/templates/pick_grid.js.j2`

## Why

The maintainer, 2026-10-29: "Comment pourrais-je faire pour supprimer un album ? Via l'interface
bien sûr. Je ne vois aucune page qui me donne la liste des albums et que je pourrais cocher pour
suppression. Et si je voulais éditer un album ? Voir les photos qu'il contient et en supprimer et,
aussi, ajouter des photos ?" Today `/albums` (0297) lists the albums and opens one; a photo is
taken out one at a time from the large view, added to another album, or made the cover. An
album only disappears when its last photo is taken out.

## What

Load the skill `photo-picking-pages` first. An opened album on the PC becomes a tile page like
browse/search, from the shared `pick_*` templates: Ctrl/Shift picking, rectangle, Ctrl+A, invert,
the keys panel, the large view; the bar gives **➖ Take out of the album** for the picking (one
request, `remove` with the keys), **Add to another album**, **Use as cover** (one photo),
**✉️ Send** and **📺 On the TV** (as in the search bar). The phone keeps today's read-only
swipe view. Taking out the last photos asks first ("the album will be empty and removed").
