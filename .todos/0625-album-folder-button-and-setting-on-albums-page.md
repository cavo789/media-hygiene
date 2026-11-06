# 0625 — Make an album's folder from its page; its setting leaves the library

- **Priority**: Medium
- **Batch**: albums
- **Depends**: —
- **Files**: `src/media_hygiene/review/templates/album_bar.html.j2`, `src/media_hygiene/review/templates/pick_bar.css.j2`, `src/media_hygiene/search/album_root_desk.py`, `src/media_hygiene/search/folders.py`, `src/media_hygiene/services/search_app.py`, `src/media_hygiene/share/album_page.py`, `src/media_hygiene/share/templates/album.html.j2`, `src/media_hygiene/share/templates/album_edit.html.j2`, `documentation/en/commands/album.md`, `documentation/fr/commands/album.md`, `documentation/en/commands/library.md`, `documentation/fr/commands/library.md`

## Decided (maintainer, 2026-11-06)

*Where should your albums go?* is configuration: it takes up to four lines in the library's
📚 Album panel, while adding to an album, the TV and sending do not use it. It only serves
`mh album <name> --apply`, the folder of hard links, which has no button on the albums page.

## Why it matters

The real use: the maintainer's wife copied photos into "À développer xxxx" folders in Explorer
to upload them to a print service. The album folder does exactly that with no duplicate, in
full quality (`share` makes reduced copies: not for printing), but today it takes a command.

## Wanted

1. Remove the setting from the album panel of the library (`album_root_path`, its script, its
   form). `/api/album-root` leaves the library's server if nothing else there uses it.
2. A button **📁 Make the folder in Explorer** on an album's page, saying: no photo is copied,
   no extra space, no duplicate. Seeing first: it shows what it will do (the dry run of
   `album`: links to make, to remove, files not found) before it acts, and states the count.
3. It asks where the albums go only when the folder is not known yet.
4. A discreet **📁 Albums folder** line on the albums page: the folder as read back from
   `config.toml`, *Change*, and *Move the N album folders made in …* (0582), moved as is.

## Watch out

- The albums page is served by the home server (`AlbumPages`), the setting by the library's
  (`FolderDesk`, `AlbumRootDesk`): the desk has to be plugged in there.
- The albums page is also shown on phones and by 24 h links: the button and the setting are
  hidden there (read-only, `data-phone`, `lan_paths`), and its writes refused by the server.
- `--apply` needs the photos without `:ro` and a persistent `/journal`: say so in one line if
  missing, never a traceback. The run prints its `undo` line.
- Tell where the album may go: same disk and same `-v` as the photos; exFAT refuses hard links.
- The page's text warns that a retouch in the album changes the original (same file).
- `docs_screenshots` should run afterwards.
