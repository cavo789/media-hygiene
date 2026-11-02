# 0548 — Phone home page: one "Albums" entry, not one button per album

- **Priority**: High
- **Batch**: phone
- **Depends**: 0547
- **Files**: `src/media_hygiene/review/templates/home_draw.js.j2`, `src/media_hygiene/services/home.py`, `src/media_hygiene/share/album_page.py`, `src/media_hygiene/share/templates/album.html.j2`, `src/media_hygiene/share/templates/album.js.j2`, `documentation/en/`, `documentation/fr/`

## Seen (maintainer, 2026-10-31)

The phone's home page shows one button per album (`tvAlbums()`, `#tvAlbums`, filled from
`ALBUM_LIST_PATH`, 0444). With 6 albums it is already long; with 50 albums, 50 buttons on a
smartphone home page: not usable.

## What

The home page stays short whatever the collection. It shows **one entry** "Albums (N)" and,
at most, the **3 albums used last** (shown or sent to the TV most recently) as shortcuts. The
entry opens the albums page — the one place where every album is listed and picked, built like
every other page (`photo-picking-pages` skill: tiles with the cover, a filter box by name,
sorted by last used, then by name).

Options to choose (needs maintainer):

- **A** — home: "Albums (N)" + the 3 last used; the rest on the albums page. (Recommended:
  one tap for what is repeated, the home page never grows.)
- **B** — home: "Albums (N)" only.

On the albums page on the phone, a tap on an album = "show on the TV" (read-only, rule
`phone-read-only`): what the home buttons do today, nothing lost.

## Also: "Sent <date>" albums pile up

Each send to the TV creates an album "Sent <date>" (`msgid "Sent {date}"`; 240 entries this
morning, and the trigger of 0547). After a month of sends: 30 albums the user never made. To
decide: a send keeps a single "Last sent" album (replaced at each send), or none at all (the
TV shows the selection, no album). Either way, they never appear among the home shortcuts.

## Tests

- 50 albums in `albums.json`: the phone home page holds one albums entry and ≤ 3 shortcuts.
- The albums page lists 50 albums, filtered by a typed name; a tap starts the TV.
- Documentation (both languages): the home page and albums pages of the phone guide; say that
  `docs_screenshots` should run.

## Decided (2026-11-02)

By the maintainer, in `/todo:iterate`: layout **A** (home: "Albums (N)" + the 3 used last; the
rest on the albums page), and a send to the TV keeps a **single "Last sent" album**, replaced at
each send, never among the home shortcuts.
