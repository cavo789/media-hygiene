# 0073 — `media-hygiene search`: find photos by words in the browser

- **Priority**: Medium
- **Batch**: tags
- **Depends**: 0072
- **Files**: `src/media_hygiene/search/` (new: query, fts, vectors, app, templates), `src/media_hygiene/index/schema.py`, `src/media_hygiene/index/` (FTS5 table kept in step with `tag_rows`), `src/media_hygiene/cli/` (new `cmd_search.py`), `src/media_hygiene/config/settings.py`, `src/media_hygiene/config/templates/config.toml.j2`, `documentation/en/`, `documentation/fr/`

## Context

0072 puts words on every photo (vision model, folder names, dates, places). The maintainer
wants to search them from a browser page ("Durbuy ours", "anniversaire gâteau", "neige 2008")
without a permanent server. The Gemini answer suggested FastAPI: not needed, `review` and
`places` already serve pages with the project's minimal asyncio HTTP server (loopback `Host`,
JSON-only `POST`).

**Overlap with Immich (0009)**: Immich's smart search (CLIP) is stronger. This page stays
small: a one-shot command over our own index, no server to keep, and the same words end up in
the XMP sidecars (0074) that Immich or digiKam can read later. If the maintainer adopts Immich
(0009, option 2), this page can stay a quick local tool or be dropped; the sidecars stay.

Checked 2026-10-10: the project's Python ships SQLite 3.46 with FTS5 and the
`unicode61 remove_diacritics 2` tokenizer.

## Proposal

- **Full text**: an FTS5 table over the tags and sentence of each file (one row per file,
  columns per source so a query can say `place:durbuy`), `unicode61 remove_diacritics 2`
  (so "noel" finds "Noël"), prefix queries ("anniv*"). Rebuilt from `tags` in seconds when
  missing or stale; never the source of truth.
- **Synonyms and plurals the model mixes** (measured in 0072: "bougie"/"bougies",
  "fleur"/"fleurs", "mer"/"bord de mer"): first the 0072 normalization; then, if the
  measurement below shows misses, `bge-m3` embeddings (already on the maintainer's Ollama,
  multilingual, milliseconds per sentence) of each sentence, stored as float32 blobs, compared
  with numpy (cosine). The query is embedded at search time. No vector database.
- **Ranking**: FTS5 `bm25` first; with vectors on, a simple merge of both lists (reciprocal
  rank fusion).
- **Page** (`search/templates/`): one search field, a grid of thumbnails (`report/thumbnails`
  previews, cached in `/cache`), each with its folder, date and tags; click → the full image;
  keyboard: `/` focuses the field, arrows move. Filters: year range, folder, source.
- **Read-only** 🔒: the page never changes a file. Optional later: "add a tag by hand" (then
  stored as `source = manual`, and written by 0074).
- **CLI**: `media-hygiene search` serves the page on an OS-chosen port like `review`;
  `search "words"` without a browser prints the first matches as a table (useful in WSL and
  in tests).

## Measurement before vectors

On the maintainer's collection, after a first 0072 night:
- [ ] 20 searches the maintainer would type; for each, hits found by FTS5 alone vs with
      `bge-m3`; note here whether vectors are worth building.

## Acceptance

- [ ] Unit tests: query parsing, diacritics, prefix, per-source columns, rebuild when stale.
- [ ] Page tests like `places` / `review` (loopback `Host` refused otherwise, JSON-only
      `POST`, CSP).
- [ ] Synthetic pictures only in tests and screenshots (`tests/support/docs/`).
- [ ] Documentation en + fr (a step of the sort guide or a reference page); `.po` translated.

## Status — PARTIAL (2026-10-11)

### Done
- `media-hygiene search` (`cli/cmd_search.py`, `services/search.py`): without words, serves
  the page on `--port` (8088) like `review`/`places` until Ctrl+C; with words
  (`search durbuy ours`), prints the first `--limit` (20) matches as a table, then suggests
  the page. Read-only 🔒 (`READ_ONLY_COMMANDS`, `PHOTO_READERS`, `PAGE_COMMANDS`: the `mh`
  launcher publishes its port and mounts the photos `:ro`).
- Full text (`search/fts.py`, `search/statements.py`): FTS5 table in the connection's
  `temp` schema, one row per file, one column per `TagSource` (`caption` included),
  `unicode61 remove_diacritics 2`, ranked by `bm25`; only tags of the current version of a
  file (size, mtime). The index is opened **read-only** (`mode=ro`: works on a `:ro` cache,
  never written); the table is rebuilt when `PRAGMA data_version` says another program
  committed (a `tags` run while the page is open). Measured: 100,000 files / 1.5 M tags
  rebuilt in ~1 s, a query in ~20 ms.
- Query (`search/query.py`): words (AND), `"phrases"`, `prefix*`, `source:word` (vision,
  caption, folder, date, place); each word also matches its French and English singular
  (`tags/plurals.py`); everything quoted for FTS5 (no syntax error possible).
- Page (`search/app.py`, `search/views.py`, `search/templates/search.html.j2`): one field,
  filters (year range on the file's date, part of the path, one source), grid with folder,
  date, sentence and word chips; `/` focuses the field, arrows move, Enter opens the large
  preview with a link to the original, Escape closes. `POST /api/search` JSON only,
  loopback `Host` only, same-origin, default CSP. Grid previews (`search/thumbs.py`) cached
  in `/cache/search-previews/` (named by path + size + mtime).
- `status` prints "Tags: N files have words, M of them from the vision model; 'search'
  finds them." (`index/tag_rows.tag_coverage`, read-only); `tags` now suggests `search`.
- Tests: `tests/unit/test_search_query.py`, `test_search_index.py`, `test_search_thumbs.py`,
  `tests/integration/tags/test_search_command.py`, `test_read_only_commands.py` (+ search).
- Docs en + fr (`reference-tags.md` section "Find a photo by its words: `search`",
  `reference-commands.md`, documentation README); `.po` translated.

### Not done
- Measurement of 20 real searches, FTS5 alone vs `bge-m3` vectors, and the vectors
  themselves (embeddings, cosine, reciprocal rank fusion).
  **Reason:** the TODO makes vectors conditional on that measurement, which needs the
  maintainer's collection and Ollama (not reachable, no network during the night run).
- "Add a tag by hand" (`source = manual`) in the page.
  **Reason:** marked optional/later by the TODO; the page stays read-only.
- FTS5 table persisted in the index (`index/schema.py`).
  **Reason:** deliberately not done: built in memory from `tags` (≈1 s per 100k files), so
  the index stays read-only and nothing can be stale on disk.
- Screenshot of the page and the help capture of `reference-commands.md`.
  **Reason:** `docs_screenshots` needs a Docker build, not run during the night session.
