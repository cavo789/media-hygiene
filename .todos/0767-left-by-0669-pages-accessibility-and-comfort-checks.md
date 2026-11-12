# 0767 — What 0669 left: Accessibility and comfort checked on every page: motion, focus, contrast, zoom

- **Priority**: Low
- **Batch**: page-shell
- **Depends**: —
- **Files**: `.todos/DONE/0669-pages-accessibility-and-comfort-checks.md`, `src/media_hygiene/review/templates/page_frame.css.j2`, `src/media_hygiene/review/templates/pick_grid.css.j2`, `src/media_hygiene/review/templates/theme.css.j2`, `tests/support/pages_browser.py`, `tests/support/pages_walk.py`

Split from section 0669 of PARTIAL 0718 (`.todos/PARTIAL/PARTIAL_0718-code-left-in-partial-todos.md`), as decided by the maintainer in the review of 2026-11-12 (one TODO per remaining section). Source TODO: `.todos/DONE/0669-pages-accessibility-and-comfort-checks.md`.

## Left (as listed in 0718; the source TODO has the full wording)

- Light `--mk-primary` on `--mk-n-50` is 4.42:1 (outline buttons on sunken chips): not
- The four checks run on every page of the walk, both themes; failures fixed or listed
- Reduced motion honoured by the frame (slideshow cross-fade included)

## How to proceed

- Check each item against the code first: some may be done already and only unticked (then say so and close them).
- File follow-ups for what is really left; every figure says *measured* or *estimated*; a new limit: say whether it should be a setting.
- Documentation EN + FR and French strings when something user-facing changes.
