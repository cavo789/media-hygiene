# 0455 — From the phone's home page, a folder or a period on the TV, not only an album

- **Priority**: Medium
- **Batch**: slideshow
- **Depends**: 0454
- **Files**: `src/media_hygiene/review/templates/home_run.js.j2`, `src/media_hygiene/review/templates/home_draw.js.j2`, `src/media_hygiene/review/album_show.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/commands/slideshow.md`, `documentation/fr/commands/slideshow.md`, `documentation/en/commands/home.md`, `documentation/fr/commands/home.md`

## Why

On a paired phone, *Show an album on the TV* lists only the saved albums (`tvAlbums`,
`home_run.js.j2`, 0444); none saved → "make one on the PC". From the couch the family wants
"the photos of last November" or "the Valkenburg folder" without an album.

## What

The phone's TV section offers three choices, each starting the show in the home server through
the path of 0454 (same cap `MAX_ADDED`, a running show replaced, the TV stays paired):

1. **An album** (as today).
2. **A folder**: the folder tree of the index (the one `browse` shows), a tap on a folder.
3. **A period**: a month (or a from/to of days) taken by the date the audit read.

Read-only, as everything off the PC (memory `phone-read-only`): it shows, never writes. "No
album saved" is no longer a dead end: folder and period are always there.

## Docs (both languages)

`slideshow.md` and `home.md` (*Your albums on the phone*): the three choices. Captures stale:
say `docs_screenshots` should run.

## Tests

Each choice → the show holds exactly the expected files; a folder outside the scanned roots or a
period without photos → a clear line, no show started; the cap refused with its message.
