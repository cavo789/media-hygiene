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
