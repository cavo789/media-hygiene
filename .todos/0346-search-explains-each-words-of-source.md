# 0346 — Search: "How to write a search" explains each choice of "Words of"

- **Priority**: Medium
- **Batch**: search
- **Depends**: —
- **Files**: `src/media_hygiene/search/templates/search.html.j2`, `src/media_hygiene/tags/models.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/commands/search.md`, `documentation/fr/commands/search.md`

## Context

Asked by the maintainer (2026-10-24): the *Words of* menu (*every source*, *seen by the model*,
*folder*, *file name*, *name of a removed copy*, *date*, *place*, *person*, *Google Photos
description*, *the model's sentence*) is not explained, on the page nor in
`/docs/fr/commands/search/`; some choices are unclear (*every source*, *removed copy*, *the
model's sentence*).

## To do

- In *How to write a search*, one line per choice, what it holds and where it comes from (the
  sources of `tags/models.py`): e.g. *name of a removed copy* — the name a duplicate had before
  `clean` removed it, kept on the copy that stayed; *seen by the model* — the words the vision
  model gave (🤖 `tags`), *the model's sentence* — its whole description, for a phrase in quotes;
  *every source* — any of them (the default).
- Each source shows whether it has words yet (e.g. *seen by the model — none yet*, 0344), and
  the equivalent prefix (`place:`, `person:` …) for typing it without the menu.
- The same table in `commands/search.md`, en + fr.

## Acceptance

- [ ] Every choice of the menu is explained on the page and in the docs (both languages).
- [ ] `docs_screenshots` to run.
