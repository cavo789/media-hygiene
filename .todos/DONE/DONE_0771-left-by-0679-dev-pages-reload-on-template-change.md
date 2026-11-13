# 0771 — What 0679 left: Developer helper: pages reload by themselves when a template or module changes

- **Priority**: Low
- **Batch**: dev-tools
- **Depends**: —
- **Files**: `.todos/DONE/0679-dev-pages-reload-on-template-change.md`, `.devcontainer/scripts/helpers/tool.sh`, `src/media_hygiene/i18n/templates.py`, `src/media_hygiene/review/respond.py`, `documentation/en/development.md`, `documentation/fr/development.md`

Split from section 0679 of PARTIAL 0718 (`.todos/PARTIAL/PARTIAL_0718-code-left-in-partial-todos.md`), as decided by the maintainer in the review of 2026-11-12 (one TODO per remaining section). Source TODO: `.todos/DONE/0679-dev-pages-reload-on-template-change.md`.

## Left (as listed in 0718; the source TODO has the full wording)

- An open tab does not reload by itself after a template-only edit (no restart, so no new
- `dive_ci` not run (no file of the image changed, so the size is unchanged by construction).
- Edit a template → the open page shows it within 2 s, no key pressed
- `dive_ci` / the image size unchanged; `development.md` EN + FR

## How to proceed

- Check each item against the code first: some may be done already and only unticked (then say so and close them).
- File follow-ups for what is really left; every figure says *measured* or *estimated*; a new limit: say whether it should be a setting.
- Documentation EN + FR and French strings when something user-facing changes.
