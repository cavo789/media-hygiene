# 0263 — `search` by meaning: CLIP image vectors, opt-in, no GPU

- **Priority**: Medium
- **Batch**: tags
- **Depends**: —
- **Files**: `src/media_hygiene/search/`, `src/media_hygiene/index/`, `src/media_hygiene/config/`, `src/media_hygiene/cli/cmd_search.py`, `tests/measure/embeddings/embedders.py`, `tests/measure/embeddings/models.py`, `pyproject.toml`, `Dockerfile`, `documentation/en/`, `documentation/fr/`

Decided by the maintainer on 2026-10-20 (0221, measured on their 1,000 photos): build search by
meaning with CLIP ViT-B/32 and its multilingual text model, opt-in.

## Why (measured, 0221)

- 67 % of the first 5 pictures relevant on 20 French searches of what is seen (SigLIP 2: 69 %,
  at twice the cost); 75 % of the good photos found among the first 24.
- 0.057 s per photo on 4 CPU threads, 1.5 GB peak memory, 0.9 GB of model files: estimated
  10 min for 10,000 photos, against 2–3.5 s per photo for Ollama's captions on the GPU.
- A model sees what, never who or where: names stay with `people`, places with the GPS.

## To do

1. **Models**: the bench's `clip` spec (`tests/measure/embeddings/models.py`, pinned revisions):
   vision ONNX + multilingual text ONNX + tokenizer + dense projection, downloaded once into
   `/cache` (never `/config`), then offline. The download is said before it starts (size), never
   silent. **Licence to check first** (to check, from the bench's note): CLIP is MIT on OpenAI's
   repository, but the Hugging Face card and the Xenova ONNX export carry none; the multilingual
   text model is Apache-2.0. Vendor the attribution as `geo/data/ATTRIBUTION.txt` does.
2. **Dependency**: `tokenizers` (the bench pip-installs `tokenizers==0.23.2` at run time):
   add it to `pyproject.toml` and measure what it adds to the image (`dive`, as 0166 did for
   `onnxruntime`, already in the image for faces).
3. **Vectors**: computed once per photo version (path, size, mtime, as every index row), stored
   in the index (a new table, schema bump, in `PATH_TABLES` so moves and pruning follow it);
   512 float32 values per photo (2 KB; 20 MB for 10,000 photos, estimated). Computed by a
   command or a step that says its time (estimated 10 min per 10,000 photos) — where it runs
   (`tags`, its own verb, or the audit when asked) is to decide while implementing; never by
   default in `audit`.
4. **Search**: `search` (and `browse`) rank by meaning when vectors exist: the query's text
   vector against the photos' vectors (cosine), merged with today's FTS5 words (names, places,
   folders) by reciprocal rank fusion, as 0084 planned; a person's name or a place then narrows
   the photos, the meaning ranks them ("Frédérique dans la cuisine" = Frédérique's photos,
   kitchens first).
5. **Setting**: off by default (`[search] meaning = false`, name to settle with the existing
   `[tags]` / `[search]` sections); the 🤖 mark where the command is pasted (a model runs locally,
   CPU only).
6. **Tests**: the bench's `StubEmbedder` style (seeded vectors, no download) for ranking, the
   fusion, moves and pruning of the vectors; the real model only in a measure, never in CI.
7. **Docs** en + fr: what it finds (what is seen), what it does not (who, where: `people`, GPS),
   the one-time download, the time per 1,000 photos.

## Settings?

Threads (`--cpus` of the bench: 4 measured) and the number of results: settings with defaults;
the model itself is fixed (CLIP), as decided.

## Gain

Estimated from 0221: a search of what is seen answers 2 of 3 first pictures right, without
Ollama, without a GPU, in about 0.06 s per photo once.
