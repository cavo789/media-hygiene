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

## Status — DONE (2026-10-19, was PARTIAL)

### Done (inbox 2026-10-19: the maintainer asked for the smoke run here)
- SigLIP 2 and CLIP run for real: `python -m embeddings.measure --models siglip2,clip`, 21
  synthetic pictures, 3 French searches, `--cpus 2`, devcontainer venv + `tokenizers==0.23.2`
  in a scratch folder, `nice -n 19`. Every pinned file downloaded (2.3 GB on disk), exit 0, the
  three pages written. Measured: SigLIP 2 0.12 s per photo (model), 0.04 s per search, load
  2.0 s, RAM peak 2.5 GB; CLIP ViT-B/32 + multilingual text 0.039 s per photo, 0.007 s per
  search, load 0.9 s, RAM peak 1.4 GB. The input/output names read from the files were right.
  Estimated for step 20 (1,000 photos, 4 CPUs): SigLIP 2 ≈ 1 min of model time, CLIP ≈ 20 s
  (scaled from 2 threads, not measured on 4), plus decoding; the download dominates.

### Earlier status — PARTIAL (2026-10-18)

### Done
- The bench in `tests/measure/embeddings/`: `measure.py` (command line), `runs.py` (sampling with
  a fixed seed, one model per spawned process, timings and RAM peak), `embedders.py` (ONNX
  runtime, preprocessing per model, `tokenizers` imported by name, a stub), `models.py` (files
  pinned to a revision, licences as checked), `ranking.py` (24 best per search, today's `search`
  among the sampled photos when an index is mounted, 50 closest pairs minus the audit's hash
  test), `pages.py` + `templates/` (summary, searches, pairs; boxes kept in local storage and
  downloaded as JSON), `README.md`. Deviation: three more modules than the `Files:` bullet
  (`embedders.py`, `runs.py`, `ranking.py`), and one page holding every search (one JSON to send
  back instead of 20).
- Models (Hugging Face API, 2026-10-18): SigLIP 2 base (`onnx-community/siglip2-base-patch16-224-ONNX`,
  Apache-2.0 on Google's card), CLIP ViT-B/32 (`Xenova/clip-vit-base-patch32`, MIT on OpenAI's
  GitHub) + `sentence-transformers/clip-ViT-B-32-multilingual-v1` (Apache-2.0 on its card, French
  among its languages), DINOv2-small (`onnx-community/dinov2-small`, Apache-2.0 on Meta's card).
  The ONNX exports state no licence: to check. Downloads: 1,536 + 894 + 89 MB = 2.5 GB, fp32.
- Step 20 of `tests/measure/mh-measure.ps1` (`-Sample`, `-Cpus`, `-Branch`): fetches the bench,
  writes the searches file with examples the first time, runs it with `C:\Photos` and the index
  read-only, models kept in `%USERPROFILE%\media-hygiene\embeddings-models`.
- Unit: `tests/unit/test_embeddings_measure.py` (19 tests, stub, synthetic pictures, no download).
- Smoke in the project's image (21 synthetic pictures, `--cpus 2`): DINOv2-small real, measured
  0.057 s per photo, RAM peak 246 MB; the tokenizers of SigLIP 2 and multilingual CLIP and the
  CLIP projection checked; pages written.

### Not done
- The smoke run of SigLIP 2 and CLIP themselves (2.4 GB of models) in the devcontainer.
  **Reason:** the unattended run was told not to download large models; their input and
  output names were read from the tails of the ONNX files (`pixel_values` → `pooler_output` /
  `image_embeds`; `input_ids` (+ `attention_mask`) → `pooler_output` / `last_hidden_state`),
  not run. Their first run is the maintainer's step 20, which 0221 waits for anyway: if it
  fails, the log names the model and the fix goes here.
