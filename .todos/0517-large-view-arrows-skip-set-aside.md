# 0517 — Large view arrows skip the photos set aside

- **Priority**: medium
- **Batch**: unassigned
- **Depends**: —
- **Files**: src/media_hygiene/review/templates/pick_viewer.js.j2, src/media_hygiene/review/templates/pick_grid.js.j2

## Context

In `mh search` (and every page built on the shared `pick_*` templates — skill
`photo-picking-pages`), a double-click opens the large view, where ← / → show the previous /
next photo. Photos already set aside are still visited; the maintainer wants the arrows to step
over them: on the first photo, with the second set aside, → shows the third.

## Acceptance

- [ ] In the large view, ← / → skip every tile currently set aside (both directions, also at
      the start/end of the list).
- [ ] Setting a photo aside while it is shown in the large view (Delete, or the button) shows
      the **previous** photo not set aside; when there is none before it, the **next** one not
      set aside; when none is left, the view closes (maintainer's choice, 2026-10-30; e.g. on
      the last photo, Delete shows the one before it). This replaces today's "set it aside, then the next
      one" (`pick_viewer.js.j2` `asideShown`, and its key labels in `pick_viewer.html.j2`,
      `pick_keys*.html.j2`, docs en + fr).
- [ ] Same behaviour on every page using the shared large view (browse, search, reviews), as the
      skill requires one large view for all.
- [ ] A test covers the skip (JS behaviour or the rendered template's navigation logic).
- [ ] Keys panel / documentation (en + fr) mention it if they describe the arrows.
