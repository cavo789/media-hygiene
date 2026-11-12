# 0764 — What 0665 left: Library page: actions grouped in a few menus, filters folded — fewer controls at once

- **Priority**: Medium
- **Batch**: search
- **Depends**: —
- **Files**: `.todos/PARTIAL/PARTIAL_0665-library-bar-and-filters-grouped-in-menus.md`, `src/media_hygiene/review/templates/pick_acting.html.j2`, `src/media_hygiene/review/templates/pick_bar.css.j2`, `src/media_hygiene/review/templates/pick_bar_panel.js.j2`, `src/media_hygiene/review/templates/slideshow_menu.html.j2`, `src/media_hygiene/review/templates/album_bar.html.j2`, `src/media_hygiene/search/templates/search.html.j2`
- **Needs maintainer**: the first CI run's real count of visible controls

Split from section 0665 of PARTIAL 0718 (`.todos/PARTIAL/PARTIAL_0718-code-left-in-partial-todos.md`), as decided by the maintainer in the review of 2026-11-12 (one TODO per remaining section). Source TODO: `.todos/PARTIAL/PARTIAL_0665-library-bar-and-filters-grouped-in-menus.md`.

## Left (as listed in 0718; the source TODO has the full wording)

- *to a folder* in Move ▾. **Reason:** no move-to-a-folder action exists on the page.
- *make from the results* / *link* in Album ▾: *📚 album of the results* stays in the left
- The browser cap (40) is an estimate until the first CI run prints the real count.
- The same menus, same order, on every tile page (the shared-parts test)
- Every action still reachable by its key; no action lost (a table old → new in the PR)
- The count of visible controls at load measured before / after, the cap in a test

## How to proceed

- Check each item against the code first: some may be done already and only unticked (then say so and close them).
- File follow-ups for what is really left; every figure says *measured* or *estimated*; a new limit: say whether it should be a setting.
- Documentation EN + FR and French strings when something user-facing changes.
- Part of this needs the maintainer (see *Needs maintainer*): do the code part, leave the rest said in the report, never guess it.
