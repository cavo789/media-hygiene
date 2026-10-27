# 0340 — Places: after "Save this position", the next folder to place opens

- **Priority**: Medium
- **Batch**: places
- **Depends**: —
- **Files**: `src/media_hygiene/places/templates/places.html.j2`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/commands/places.md`, `documentation/fr/commands/places.md`

## Context

Reported by the maintainer (2026-10-24): picking a folder in *To place*, then *Save this
position*, moves it to *Placed* (right), but they must then scroll the left column back up to
find the next one to place — at every folder.

Today (`actOnFolder`): the save closes the drawer, redraws both lists and flashes the saved line
in *Placed* (`folderFlash`), unfolding it: the reader's eye is sent away from *To place*.

## To do (proposal, to confirm with the maintainer at review)

- After a save (or *Not a town*), the **next folder of *To place*** (the one that followed it in
  the shown order, same filter) opens at once in the drawer, its line scrolled into view
  (`scrollIntoView({ block: "nearest" })`); the status line says `Saved: Durbuy. Next: Ciney
  (12 left)`.
- Keys in the drawer: `N` / `→` next folder to place, `P` / `←` previous, `Enter` saves; listed in
  the ⌨ panel.
- The saved line is no longer flashed in *Placed* (still reachable: it is there, with 📌).
- The last folder saved: *Nothing left to place* and the drawer closes.

## Acceptance

- [x] Saving five folders in a row needs no scroll and no click in the list.
- [x] The filter typed is kept: *next* is the next one matching it.
- [x] Docs en + fr; `docs_screenshots` to run (not run).
