# 0826 — Put the Show/Hide panel toggle on the left panel's edge

- **Priority**: medium
- **Batch**: unassigned
- **Depends**: —
- **Files**: src/media_hygiene/review/templates/tile_view.html.j2, src/media_hygiene/review/templates/tile_view.js.j2, src/media_hygiene/review/templates/tile_view.css.j2, src/media_hygiene/search/templates/search_bar.css.j2, src/media_hygiene/people/templates/people.css.j2, the page frame templates (rule `.claude/rules/pages.md`)

## Context

The `◀ Hide the panel` / `▶ Show the panel` button (`#sideToggle`, shared `tile_view.html.j2`)
sits at the far right of the toolbar (screenshot of /library, 2026-11-15), far from the left
area it opens and closes, next to the purple vertical menu. The maintainer needed two seconds to
find it: on the web, such a collapse toggle (accordion) sits on the edge of the area it controls.
The change goes in the shared part so it applies to 100 % of the pages that show the left
vertical menu / left panel (pick_acting pages: library, browse, person, phone…; people; near,
gone, pairs reviews) — rule *feature follows its kind*: list each page checked in the report.

## Acceptance

- [ ] The toggle sits on the left area's edge (a small ◀/▶ handle attached to the panel, beside the purple vertical menu), visible both when the panel is shown and hidden; no longer at the right of the toolbar.
- [ ] Same markup and place on every page that has the left menu/panel (shared template, no page-local copy); every such page listed in the report.
- [ ] Keyboard reachable, `aria-expanded` + `aria-controls`, label/tooltip kept through `_()` (FR `.po` updated).
- [ ] State still remembered per page (`tile_view_key`); S/M/L/XL switch keeps working where it is.
- [ ] Page-contract tests pass; say that `docs_screenshots` should run (captures stale), docs EN/FR mention updated if they name the button's place.
