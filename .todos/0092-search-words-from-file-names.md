# 0092 — `search`: the words of the file name, not only those of the folders

- **Priority**: Medium — a user typing the name of a file expects to find it (review of 0079, 2026-10-11)
- **Batch**: tags
- **Depends**: —
- **Files**: `src/media_hygiene/tags/producers.py`, `src/media_hygiene/tags/models.py`, `src/media_hygiene/plan/name_rules.py`, `src/media_hygiene/services/tags.py`, `src/media_hygiene/search/`, `documentation/en/reference-tags.md`, `documentation/fr/reference-tags.md`, `documentation/en/commands/search.md`, `documentation/fr/commands/search.md`, `tests/unit/test_tag_producers.py`, `tests/integration/tags/`

## Context

`search "anniversaire"` does not find `Vidéos/Anniversaire.mp4`: the free tags come from the
folders between the root and the file (`TagSource.FOLDER`, `tags/producers.folder_words`),
the date, the place and the vision model. The file name gives no word. The maintainer finds
this annoying: a file should be found by its own name as well as by its folder.

Most names carry nothing: `IMG_1234.jpg`, `DSC00042.JPG`, `VID-20190712-WA0001.mp4`,
`PXL_20230101_120000.jpg`. The keep policy already recognizes them
(`plan/name_rules.has_generated_name`).

## Goal

- A new source `TagSource.NAME` ("name"): the meaningful words of the file name (its stem),
  split like the folder words (`_SEPARATORS`, `context.words.keeps`, month words and link
  words left out), nothing for a generated name, numbers and dates left out (the date has
  its own source).
  `Anniversaire Léa.mp4` → `Anniversaire`, `Léa`; `IMG_1234.jpg` → nothing;
  `2019-07-12 Plage (petite).jpg` → `Plage`, `petite`.
- Recomputed like the other cheap sources by `tags` (no model, no photo read): the index
  holds the paths. Videos included (they have a name even without a description).
- `search` finds a file by a word of its name, through the same FTS table.
- `xmp`: decide whether NAME words are written to `dc:subject` like FOLDER words (probably
  yes, same nature).

## Acceptance

- `tags` then `search anniversaire` finds `Anniversaire.mp4` in the docs library.
- Generated names give no tag; a test per pattern of `name_rules`.
- Docs (en + fr): the list of tag sources in `reference-tags.md`, `commands/search.md`.
