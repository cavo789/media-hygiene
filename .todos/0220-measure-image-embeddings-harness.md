# 0220 — Image embeddings: a measurement bench (two models, N photos, French searches → pages to judge)

- **Priority**: Low
- **Batch**: tags
- **Depends**: —
- **Files**: `tests/measure/embeddings/measure.py` (new), `tests/measure/embeddings/models.py` (new), `tests/measure/embeddings/pages.py` (new), `tests/measure/embeddings/README.md` (new), `tests/unit/test_embeddings_measure.py` (new)

## Context

Chosen by the maintainer on 2026-10-17 (proposal F11: "let's try with a TODO"). Today `search`
finds a photo by words: its folders, names, date, place, people, and — when a local vision model
ran — its description (Ollama: 2 to 3.5 s per photo on the maintainer's GPU, measured 2026-10-10:
tens of hours for a whole collection). An image embedding model turns each photo into a vector;
a sentence ("gâteau d'anniversaire") becomes a vector of the same space; the nearest photos answer,
without any word written for them. Immich's smart search works this way (CLIP). The same vectors
find near duplicates that perceptual hashes miss (crops, filters, mirrored copies): Video Duplicate
Finder uses DINOv2 for that (≈ 50 ms per file on a CPU, ≈ 100 MB downloaded once: its README,
2026-10-17). ONNX Runtime is already in the image (`people`).

Related: 0084 (BLOCKED: `bge-m3` vectors over Ollama's captions, waiting for a `tags` night). If
image embeddings find what words miss, 0084 may become unneeded: 0221 decides both.

## What to do

A measurement bench in `tests/measure/embeddings/`, never part of the published image:

- **Models**, two to compare (licence, ONNX export and size to check before writing any code; no
  model under a non-commercial licence, as 0090 decided for faces):
  1. Google SigLIP 2, base size: multilingual, Apache-2.0 according to a derived model card (to
     confirm on Google's own card);
  2. OpenAI CLIP ViT-B/32 (MIT) with a multilingual text encoder trained to match it (licence to
     check).
  For near duplicates only, a third, image-only: DINOv2-small (licence to check).
- **Run**: in a container from the project's image, extra wheels (a tokenizer) installed in a
  temporary environment at run time; the photos mounted `:ro`; the models downloaded into a folder
  given on the command line (reused between runs, never under `/config`); `N` photos sampled with a
  fixed seed; `--cpus` honoured.
- **Searches**: a text file of queries, one per line (the maintainer writes 20 in French).
- **Output**, an HTML folder: per query, the 24 best photos of each model side by side (and today's
  `search` hits on the same photos when an index is mounted), each picture a checkbox "relevant"
  saved into the page's own JSON download; per model: seconds per photo, threads, RAM peak, model
  size; a page of the 50 closest pairs that the audit does not already call near duplicates.
- `README.md`: the one PowerShell line for the maintainer (the full `docker run`, with
  `C:\Photos` read-only), what it downloads, how long it takes (estimated from the smoke run).

## Explicit non-goals

- Anything in `src/`: the decision (0221) comes first.
- A GPU: CPU only, as the target users have.

## Acceptance

- Unit (`test_embeddings_measure.py`): the sampling, the page writer and the pairing with a stub
  model (random vectors), no download.
- One smoke run in the devcontainer with the real models on 20 synthetic pictures (`--cpus 2`,
  `nice`): it ends, the pages open, the timings are written; report the download sizes and the
  seconds per photo (measured, synthetic pictures).

## Gain

None by itself: it lets the maintainer judge, on their own photos and searches, whether "search by
meaning" is worth building, and at what cost per photo.
