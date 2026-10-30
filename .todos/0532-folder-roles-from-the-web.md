# 0532 — Folder roles (protected, preferred, backup, excluded) set from the web pages

- **Priority**: High
- **Batch**: one-interface
- **Depends**: —
- **Files**: `src/media_hygiene/search/folders.py`, `src/media_hygiene/search/folder_tree.py`, `src/media_hygiene/search/templates/`, `src/media_hygiene/places/toml_edit.py`, `src/media_hygiene/config/folder_roles.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/`, `documentation/fr/`

## Asked (maintainer, 2026-10-30)

"If this feature is not shown in the web interface, it is as if it did not exist. A user only
learns about it if they see it."

## Today

`protected`, `preferred`, `backups` and `excluded` (`config.toml`, first section) are only set by
editing the file or per run (`--protect`, `--prefer`, `--backup`, `--exclude`). No page shows
which folders hold a role, nor lets the user change it (checked: no route writes these keys;
only `places`, `people` and the classify rules write `config.toml`, through `toml_edit`).

## Wanted

- The folder tree of the pages (search's `GET /api/folders`) shows each folder's role with a
  badge (🛡️ protected, ⭐ preferred, 💾 backup, 🚫 excluded) and a one-line explanation on hover.
- A folder's menu offers *Role of this folder*: none / protected / preferred / backup / excluded,
  each with its consequence in one sentence (protected: "never changed; identical files
  elsewhere are set aside").
- Saved with `toml_edit` (comments kept, atomic), then **read back from disk** and shown; a role
  that clashes with another (`check_backup_roles`, `overlap`) is refused with the reason.
- The home page tells, once, that a master library can be protected, linking to that menu.
- A role change makes the last audit's proposals stale: say so and offer to re-run the audit.
- What happens when a protected folder is renamed in Explorer: the role points nowhere — show
  it in the tree as a missing folder with *Remove* (workflow rule on path-keyed data). Test it.
- Docs in both languages; `docs_screenshots` to run afterwards.
