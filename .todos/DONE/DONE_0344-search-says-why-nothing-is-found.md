# 0344 — Search says why "chat" finds nothing: no photo described yet

- **Priority**: High — the search looks broken until `tags` has run
- **Batch**: search
- **Depends**: —
- **Files**: `src/media_hygiene/search/app.py`, `src/media_hygiene/search/fts.py`, `src/media_hygiene/search/meaning.py`, `src/media_hygiene/services/search_pages.py`, `src/media_hygiene/search/templates/search.html.j2`, `src/media_hygiene/search/templates/search.js.j2`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/commands/search.md`, `documentation/fr/commands/search.md`

## Context

Reported by the maintainer (2026-10-24): `chat`, `vieil homme`, `"bord de mer"` (the example of
*How to write a search*) find nothing, though they have many beach photos.

## Likely cause (read in the code and the maintainer's console, to confirm)

Their `tags` run stopped at the question (`40,099 photos to describe…`, 0343): the index holds
the words of folders, names, dates, places and people only (`44,488 files: 203,246 words`). What
a photo **shows** comes from the vision model (`vision` source) or from search by meaning
(`[tags] meaning`, CLIP vectors) — neither exists yet, so `chat` matches only a file or folder
named so. The page never says it.

## To do

- The page knows what the index holds: how many files have vision words, whether meaning
  vectors exist. When none (or few) are there, the line under the search says it once: *What
  the photos show is not known yet: 0 of 44,488 described. Words found today come from folders,
  names, dates, places and people.* + 👉 the step that fills it (*Describe the photos*, 🤖).
- *Nothing found* for a search says which part found nothing when the cause is known (a word
  only the model could give).
- The *How to write a search* example uses a word every index has (a place), or says that the
  example needs the photos described.

## Acceptance

- [ ] An index without tags: searching `chat` explains why and what to run.
- [ ] An index with tags: no such line.
- [ ] Docs en + fr say what is found before and after `tags`; `docs_screenshots` to run.
