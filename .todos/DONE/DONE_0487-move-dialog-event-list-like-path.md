# 0487 — Move to an event: list the existing folders like "Path contains"

- **Priority**: Medium
- **Batch**: search
- **Depends**: —
- **Files**: `src/media_hygiene/search/templates/move_dialog.html.j2`, `src/media_hygiene/search/templates/move_dialog.js.j2`, `src/media_hygiene/search/templates/search_path_list.js.j2`, `src/media_hygiene/search/templates/search.html.j2`

On the search page, the **Event** button opens "Move to an event". Its "Event folder name"
field offers the event folders already present in the target month (e.g. `2013/2013-03`) —
the maintainer likes that list a lot — but it is a native `<datalist id="moveNames">`: the
browser draws it as a small floating tooltip, detached from the field, narrow, in another
font (seen 2026-10-29, Chrome/Edge on Windows).

Wanted: the same drop-down as **Path contains** (`search_path_list.js.j2`): a list attached
under the field, its full width, the page's font, a scrollbar, one line per folder.

- Reuse the Path contains list (move the shared part to a helper rather than copy it — the
  duplicate-code hook at push refuses a copy); drop the `<datalist>`.
- One line per existing event folder, with its file count when known (as Path contains
  shows); typing filters; Up/Down/Enter/Escape and a click choose, as in Path contains.
- A ✕ empties the field and shows the list again (as commit d3c5261f did for Path contains).
- The field keeps accepting a new name not in the list.
- Same look on the other datalists if cheap (`album_bar` `albumNames`, `people` `names` /
  `whoList`, `categories`): say in the report which were converted; a follow-up TODO otherwise.

Done when: the dialog's list looks and behaves like Path contains (screenshot), tests of the
move dialog pass, `docs_screenshots` flagged as needed if a capture shows the dialog.
