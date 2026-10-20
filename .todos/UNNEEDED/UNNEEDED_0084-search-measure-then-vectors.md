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

## Status — BLOCKED (2026-10-11)

### Not done
- All items remain open; nothing speculative was built.
  **Reason:** the decision rests on 20 real searches over real tags, which need 0082 (prompt
  benchmark) then a first real `tags` night. Procedure for the maintainer:
  1. After 0082: `mh tags --path "C:\Photos"` (a night; `--yes` skips the question).
  2. `mh search` (page) or `mh search <words>` (table), 20 searches you would type: people's
     events (`anniversaire Léa`), places (`Durbuy`, `mer`), objects (`gâteau`, `vélo`),
     seasons (`neige 2010`). Since 0092 the words of the file names count too.
  3. For each: hits found, and the photos missed that you expected (open the folder).
     Classify each miss: plural/spelling (→ `plurals.py`), stop word, synonym ("mer" /
     "bord de mer", → a small synonym list), or truly semantic (→ vectors).
  4. Write the table here; build `bge-m3` vectors (plan above) only if the semantic misses
     dominate.

## Closed (2026-10-20)

UNNEEDED: the image embeddings measured by 0221 answer searches by meaning without Ollama's
captions (CLIP: 67 % of the first 5 relevant, 0.06 s per photo on the CPU, no GPU); built by
0263. Decided by the maintainer on 2026-10-20.
