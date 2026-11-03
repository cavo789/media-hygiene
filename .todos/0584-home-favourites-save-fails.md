# 0584 — Starring an action on the home page: "The favourites could not be saved in config.toml"

- **Priority**: High
- **Batch**: home
- **Depends**: —
- **Files**: `src/media_hygiene/cli/home_favourites.py`, `src/media_hygiene/review/home_favourites_api.py`, `src/media_hygiene/review/templates/home_favs.js.j2`, `src/media_hygiene/places/toml_edit.py`

## Asked (maintainer, 2026-11-03)

On the home page (Windows, Docker Desktop), clicking the ☆ of an action (*Retrouver une photo
par ses mots*) shows the toast "Les favoris n'ont pas pu être enregistrés dans config.toml."

## Found so far (2026-11-03, reading the code, nothing run on Windows)

- `save_favourites` on a fresh default `config.toml` works (run here: `('search', 'audit')`
  read back). So the failure depends on the user's file or the running server.
- The toast is shown for **any** non-OK answer (`home_favs.js.j2`: `reply.body.error ||
  T.favFailed`): a 403 (`Origin` ≠ `http://<Host>`, e.g. the page opened through another
  address), 415, 405 (`config_file` is `None` → route falls to `METHOD_NOT_ALLOWED`), or the 500
  of an `OSError`/`ValueError` in the write. The user cannot tell which: the real cause is lost.
- **Separate data-loss bug found on the way**: `table_of` only reuses a `tomlkit` `Table`. When
  `[home]` is split (an `[home.x]` after another section), tomlkit returns an out-of-order proxy,
  `table_of` replaces it with a new table, and `[home.x]` is **silently dropped** from the file
  (reproduced: `[home] / [scan] / [home.more]` → `home.more` gone after a save). The same helper
  writes `places`, scopes and import steps: all can lose user settings the same way.

## Cause found and fixed (2026-11-03)

The maintainer's network tab: `POST /api/favourites` → **405**, with no `[home]` in their
`config.toml`. The home server routes only `_HOME_PATHS` to `HomeApp`, every other path to
`search`; `/api/favourites`, `/api/scan-scope` and `/api/import-steps` were missing, so all three
saves of the home page failed in the real image (unit tests call `HomeApp` directly). Fixed:
`review/home_paths.py` (`HOME_PATHS`), and `tests/unit/test_home_paths.py` checks that every path
`HomeApp` compares is in it. Left below: the toast that hides the status, the `table_of` loss.

## To do

1. ~~Reproduce~~ (done above); log the exception of a failed write (never shown as a trace).
2. Toast: say which case (not allowed from this address / file not writable / file not readable)
   instead of one message for every status.
3. `table_of`: accept any mapping tomlkit gives (out-of-order proxy, super table) and never
   replace an existing table; one test per shape (split table, dotted keys `home.favorites = [...]`,
   inline table `home = {…}`), each proving the other keys survive the save.

## Acceptance

- [x] Starring works (confirmed by the maintainer 2026-11-03, star and reordering kept) on the maintainer's setup, the star read back from disk
- [ ] A failing save says why
- [ ] No save through `toml_edit` drops a key it did not write (tests above)
