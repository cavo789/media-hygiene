# 0484 — Home page favourites: starred actions, reorderable

- **Priority**: Medium
- **Batch**: home
- **Depends**: 0483
- **Files**: `src/media_hygiene/review/home_parts.py`, `src/media_hygiene/review/home_app.py`, new `src/media_hygiene/cli/home_favourites.py`, `src/media_hygiene/cli/menu_catalog_*.py`, `src/media_hygiene/config/`, `src/media_hygiene/review/templates/home.js.j2`

The maintainer opens the same actions all the time (search, import). Let each user pin them.

- A ☆ on every action of the menu and of the command palette adds or removes it.
- The home page shows a row of large cards (icon and label from the menu catalog). With none,
  three are suggested: Library (ex-search), Import, Audit.
- Reorder by drag and drop (mouse and touch); keyboard: Alt+←/→ on the focused card.
- Stored in `config.toml`, `[home] favorites = ["search", "import"]`, written with tomlkit as
  `places` does (comments kept, atomic write); `POST /api/favourites` (JSON only, loopback
  `Host`); the saved list is read back from disk and drawn (never "saved" from memory).
- An unknown action name in the file is ignored (renamed or removed verb), not an error.
- Tests: save then read back, order kept after a move, unknown name ignored, file comments kept.
- Read-only off the PC (phone): stars not shown there.
