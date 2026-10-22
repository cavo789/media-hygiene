# 0295 — Albums: a named, logical selection of photos, apart from what is set aside

- **Priority**: Medium — the base of the *Share* area (0294): the TV, the phone and the sending all start from an album
- **Batch**: share
- **Depends**: 0294
- **Files**: `src/media_hygiene/share/albums.py` (new), `src/media_hygiene/share/album_api.py` (new), `src/media_hygiene/search/app.py`, `src/media_hygiene/search/templates/search.html.j2`, `src/media_hygiene/search/templates/browse.html.j2`, `src/media_hygiene/search/templates/browse.js.j2`, `src/media_hygiene/review/templates/review.html.j2`, `src/media_hygiene/review/lan_app.py`, `src/media_hygiene/services/slideshow_pick.py`, `src/media_hygiene/cli/cmd_slideshow.py`, `src/media_hygiene/paths/locations.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/commands/`, `documentation/fr/commands/`

## Context

Designed in chat with the maintainer (2026-10-22), for the *Share* area (0294). Every way to
share (the TV, a phone at home, an e-mail, a social network) needs a selection of photos, often
from several folders (a holiday spread over days and cameras). `search` and `browse` already
pick across folders, but what they pick is **set aside to be removed**: the `chosen` key of the
decisions file, applied by `clean --decisions` (quarantine). `slideshow --chosen` (0291) reuses
that list: showing on the TV what one meant to throw away. Sharing and discarding must never
share a list.

## Decided (2026-10-22, the maintainer, in chat)

- An album is a **logical grouping**: a list of references to the user's files. Nothing is
  copied, nothing moved. Copies exist only when the user asks to prepare an album for sending
  (0296), resized, in a folder of their own.
- Stored as a **file in `/reports`** (`albums.json`, like `decisions.json` and
  `sort-decisions.json`), **not in the SQLite index**: the index is a cache under `/cache`,
  rebuilt from the files and safe to delete; an album is the user's choice and must survive it.
  Each save read back from the disk and shown (the product rule).

## What to do

1. `albums.json`: named albums (e.g. "Crete 2023"), each a list of entries `{path, sha256,
   added}`; atomic write, read back; a schema version.
2. **A file that moved** (`.claude/rules/workflow.md`): the tool's own moves (`sort`, `undo`,
   the quarantine) and the user's (a folder renamed in Explorer). An entry whose path is gone is
   found again by its SHA-256 in the index (the digest the audit already keeps); found → the
   path is updated and saved; not found → shown as missing on every album page, never dropped
   silently. One test per event (rename, move by `sort`, quarantine then `undo`, deleted).
3. **➕ Add to the album** in `search`, `browse` and the burst review: the files picked, or
   every file found; choose or create the album by name; remove from it. A separate control
   from *Set aside*, never the same list.
4. A **paired phone** (0269) may add to and remove from an album (it touches no photo): the
   only write a phone gets besides the audit; `Origin` checked as for the rest.
5. `slideshow --album <name>` replaces `--chosen` (kept one release with a line saying to
   use an album; to decide whether to drop it at once).
6. Docs en + fr (search, browse, slideshow, the *Share* area), translations, `docs_screenshots`
   afterwards.

## Acceptance

- An album holds photos of several folders; nothing on the disk changes but `albums.json`.
- The tests of item 2 pass: a moved file is found again, a deleted one is said missing.
- *Set aside* and *Add to the album* never touch each other's list (a test).
- `slideshow --album "Crete 2023"` shows exactly that album.
