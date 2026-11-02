# 0549 — Move: drop the `[[places.folders]]` of an emptied folder; the dialog's buttons always visible

- **Priority**: High
- **Batch**: search
- **Depends**: none
- **Files**: `src/media_hygiene/services/sort_links_folders.py`, `src/media_hygiene/places/config_folders.py`, `src/media_hygiene/search/templates/move_dialog.html.j2`, `src/media_hygiene/search/templates/move_dialog.js.j2`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/`, `documentation/fr/`

## Seen (maintainer, 2026-10-31)

"Move to an event" dialog of the search page, after moving 466 photos of
`C:\Photos\2017\Juillet 2017\Vacances Dordogne\…` to `C:\Photos\2017\2017-07\Dordogne`:

1. The result ends on: *"[[places.folders]] names C:\Photos\2017\Juillet 2017\Vacances
   Dordogne\Figeac, that this run emptied: point it to the photos' new folder in config.toml,
   or remove it."* (`sort_links_folders.py`). `config.toml` did hold:

   ```toml
   [[places.folders]]
   folder = 'C:\Photos\2017\Juillet 2017\Vacances Dordogne\Figeac'
   latitude = 44.609
   longitude = 2.032
   ```

   Asking the user to edit `config.toml` by hand is useless work: the tool knows the folder is gone.

2. The list of source folders and the long result text push the dialog's `<menu>` (`#moveNo`
   Close, `#moveGo` Move, greyed) out of view: no way to close the dialog but Escape.

## What

1. When a move (or `sort`) leaves a folder named by a `[[places.folders]]` entry empty or gone,
   remove that entry from `config.toml` automatically (tomlkit, comments kept, atomic — like
   `places/config_folders.py`), read it back from disk, and say it in one line ("Place of
   `…\Figeac` removed from config.toml"). The "point it / remove it" sentence goes.
   To decide while implementing (say it in the report): when every photo of the folder went to
   one single new folder, moving the entry there (keeping the place) may be better than removing
   it; propose it if cheap.
   Also on `undo`: the run's journal records the removed entry, so `undo` puts it back.
2. The dialog's buttons stay visible whatever the text length: the dialog is a column with a
   fixed header and `menu`, the middle (folder list + result) scrolls (`max-height` on the
   dialog, `overflow:auto` on the body only). Check at phone width too.

## Acceptance

- After a move emptying a `[[places.folders]]` folder, `config.toml` no longer holds it (read
  back from disk), comments of the file kept; `undo` restores it.
- With 50 source folders and the longest result, Close is visible and clickable without scrolling.
- `i18n_update` + FR translation; docs EN/FR updated if they quote the old sentence;
  `docs_screenshots` should run (not run unasked).

## Tests

- Unit: entry removed / kept when the folder still holds files; comments preserved; undo restores.
- Template: the menu sits outside the scrolling area.
