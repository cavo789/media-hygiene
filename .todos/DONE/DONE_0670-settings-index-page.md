# 0670 — One *Settings* entry listing every setting, each opening on its page

- **Priority**: Low
- **Batch**: settings-on-pages
- **Depends**: —
- **Files**: `src/media_hygiene/review/setting_groups.py`, `src/media_hygiene/review/page_settings.py`, `src/media_hygiene/review/templates/shell_side.html.j2`, `src/media_hygiene/review/home_app.py`

Filed by the UX / speed / security review of 2026-11-10 (asked by the maintainer; analysis only, no code changed).

## Decided (2026-11-10, maintainer)

- **Yes, an index**: a *⚙ Settings* entry listing every setting, each row opening the setting
  on its page; no second place to edit. It also lists the settings still in `config.toml` only.

## Context

The design chosen (0536–0538, 0606–0609): a setting lives **on the page it changes**
(strictness on the reviews, grouping on Events, language in the header). Good while working;
but a user who wonders "where do I change X?" has no place to look — `/settings` answers
404 (*measured*, 2026-11-10) and the full list is `config.toml`. Memory rule *visible in
web or nonexistent*: a setting only in `config.toml` counts as missing.

Before changing a chosen design: this proposal **keeps** the settings on their pages and
only adds a way to find them. It loses nothing; it adds one entry in the shell's menu.

## Proposal

- *⚙ Settings* in the shell's side: one page listing the groups of `setting_groups.py`
  (name, current value read from disk, one line of what it does), a search field, each row a
  link opening the setting **on its page** (the group unfolded). No second place to edit.
- At the bottom: the settings that exist in `config.toml` only, listed as such, counted —
  the backlog of *visible in web* made visible (each a candidate TODO, not part of this one).

## Acceptance

- [ ] The page lists every group; a test fails when a group of `setting_groups.py` is not on it
- [ ] The count of `config.toml`-only settings shown, with their names
- [ ] Docs EN + FR; `docs_screenshots` should run

## Where the user gains

Before: a setting is found by knowing its page, or by reading `config.toml`. After: one
searchable list, values read from disk.

## Status — DONE (2026-11-11)

- `/settings/` on the home server (`services/settings_here.py`, PC only, `GET` only: it writes
  nothing), *⚙ Settings* in the shell's side (`shell_side.html.j2`, pages of the home server).
- 17 rows (`services/settings_rows.py`): the 3 groups of `setting_groups.py` first (language,
  slideshow pace, events grouping), then the other values pages write (local AI, disk space,
  scan scope, phones, import steps, home page, folder roles, albums folder, sorting, burst and
  junk strictness, places, event rules, tags). Each value read from `config.toml` at each
  request (`services/settings_index.py`), *default* when the file does not hold it.
- Search field, its text in the URL (`?q=`, `mhView`); the events page unfolds *Group the
  photos…* on `#grouping`; the language row points at the bar's picker of the page itself.
- *In config.toml only*: every key of `Settings` no row names, listed and counted: 89 keys
  (measured, `config_only(setting_rows())`, 2026-11-11).
- Tests: `tests/unit/test_settings_index.py` (every group has its row with its keys, every row
  key is a setting, rows + rest = the model, value/default from disk, hostile value as text,
  route GET/redirect/405/no write); the page added to `PAGE_STEPS` (headers, frame, hostile
  names via `tests/support/page_render.py`).
- Docs EN + FR: `commands/home.md` *Every setting* / *Tous les réglages*. `docs_screenshots`
  should run.
