# 0084 — `search`: measure 20 real searches, then decide on `bge-m3` vectors

- **Priority**: Low
- **Batch**: tags
- **Depends**: 0082
- **Files**: `src/media_hygiene/search/fts.py`, `src/media_hygiene/search/statements.py`, `src/media_hygiene/search/` (new `vectors.py` if built), `src/media_hygiene/index/schema.py`, `src/media_hygiene/config/settings.py`, `src/media_hygiene/config/templates/config.toml.j2`, `documentation/en/reference-tags.md`, `documentation/fr/reference-tags.md`

## Context

TODO 0073 (closed) delivered `media-hygiene search` on full text only: an FTS5 table built in
memory from the `tags` rows at each start (`unicode61 remove_diacritics 2`, one column per
`TagSource`, French and English singulars searched too). Vision models mix synonyms and
near phrases ("mer" / "bord de mer", "gâteau" / "gâteau d'anniversaire"): FTS5 may miss them.
0073 made semantic vectors conditional on a measurement on the real collection, which needs real
tags first (0082, then a `tags` night).

## Measurement

- [ ] After a first real `mh tags` night: 20 searches the maintainer would type (people's
  events, places, objects, seasons). For each, note the hits FTS5 finds and the photos it
  misses that a person would expect (look in the folder).
- [ ] Note the results here. Decision: build vectors only if FTS5 misses many expected photos
  that a better normalization (plurals, `stop_words`, a small synonym list) would not fix.

## If vectors are built

- [ ] `bge-m3` embeddings (already on the maintainer's Ollama, multilingual) of each caption,
  stored as float32 blobs in the index, keyed like the tags (path, size, mtime, model); cosine
  with numpy; the query embedded at search time. No vector database.
- [ ] Ranking: FTS5 `bm25` merged with the vector list by reciprocal rank fusion.
- [ ] Off by default: an `[tags] embed_model` (empty: no vectors, nothing sent).
- [ ] Unit tests with a fake Ollama embedding endpoint; docs en/fr.

## Acceptance

- The 20 measured searches and the decision written in this TODO; vectors built only if they
  find what FTS5 missed.
