# 0486 — Rename the search page to Library (Photothèque)

- **Priority**: Low
- **Batch**: search
- **Depends**: —
- **Files**: `src/media_hygiene/cli/menu_catalog_find.py`, `src/media_hygiene/cli/`, `tests/support/docs/scenario.py`, `.config/mkdocs/mkdocs.yml`, `documentation/en/commands/`, `documentation/fr/commands/`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`

The search page has become the central page: search and browse. Name chosen by the maintainer
(2026-10-29): **Library / Photothèque**.

- New verb `mh library`; `search` kept as a hidden alias (scripts, habits).
- Page title, menu catalog entry, home cycle, links; command page in both languages, its name in
  `COMMANDS_TOO`, mkdocs `nav` (old URL redirected or kept as a stub page).
- Check that no other verb is already called `browse`/`library` (to check).
