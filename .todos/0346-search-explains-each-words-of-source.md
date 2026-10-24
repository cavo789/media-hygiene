# 0346 — Search: "How to write a search" explains each choice of "Words of", with short tips

- **Priority**: Medium
- **Batch**: search
- **Depends**: —
- **Files**: `src/media_hygiene/search/templates/search.html.j2`, `src/media_hygiene/tags/models.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/commands/search.md`, `documentation/fr/commands/search.md`, `src/media_hygiene/services/search_pages.py`, `documentation/en/reference-tags.md`, `documentation/fr/reference-tags.md`

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

### Tips for searching (asked by the maintainer, 2026-10-24)

The maintainer typed `un vieil homme` after two hours of `tags` and found nothing. Read in the
code, four reasons, none said anywhere:

1. **Every word typed must be found** (`search/query.py`, `match_expression` joins the terms
   with AND): `un` and `vieil` and `homme`. Articles count as words.
2. **The model never writes an age, a sex or a relationship**: its prompt
   (`classify/ai/templates/tags_fr.txt`, `tags_en.txt`) allows only *adulte / enfant / bébé /
   groupe* for people. `vieil homme`, `grand-mère`, `femme` are never among its words; a person
   is found by their name (`people`) or by meaning.
3. **A whole sentence works only with search by meaning** (`tags --meaning`, off by default):
   without it, type one to three words, the shortest that tell the photo.
4. **The model's words reach the search at the end of the `tags` run** (or after one Ctrl+C,
   which writes the words of the photos described so far). Drop this tip if 0353 (words written
   as each photo is described) is done first.

On the page, **very short**: in *How to write a search*, three lines at most, above the source
list, e.g. (en; the French through `_()`):

- *Every word must be found: type one to three words (`plage`, `gâteau bougie`), not a
  sentence.*
- *People are `adulte`, `enfant`, `bébé`, `groupe` for the model; find someone by their name.*
- *A sentence ("an old man in a garden") needs search by meaning: 🤖 `tags --meaning`.*

When search by meaning is on (vectors exist), the third line says so instead (*sentences
work*). The page states, it does not repeat what 0344's "nothing found" line already explains.

In `commands/search.md` (en + fr): a section *Tips for finding a photo* after *What you can
type*: the four reasons above with an example each (a search that fails → the one that works),
and what to try when nothing is found (fewer words, a prefix `anniv*`, another source, `--meaning`).
`reference-tags.md` links to it.

## Acceptance

- [ ] Every choice of the menu is explained on the page and in the docs (both languages).
- [ ] The page's tips fit in three lines and change with search by meaning on or off (test both).
- [ ] The docs' tips section exists in en + fr, with a failing and a working example per tip.
- [ ] `docs_screenshots` to run.
