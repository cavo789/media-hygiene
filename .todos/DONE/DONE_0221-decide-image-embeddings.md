# 0221 — Decide on image embeddings (search by meaning, near duplicates) from the maintainer's run of 0220

- **Priority**: Low
- **Batch**: tags
- **Depends**: 0220
- **Files**: TBD
- **Needs maintainer**: one run of the bench of 0220 on 1,000 photos of `C:\Photos` (read-only) with 20 searches written in French, then the "relevant" boxes ticked in its pages (about an hour, estimated: 20 queries × 2 models × 24 pictures to look at)

## Context

Chosen by the maintainer on 2026-10-17 (proposal F11). 0220 builds the bench; only the maintainer
can judge whether the photos found are the ones a person would expect, on their own photos (an
unattended run never reads them). The same run answers 0084 (BLOCKED: text vectors over Ollama's
captions): if image embeddings find what words miss, 0084 is closed as unneeded.

## What to do

1. The maintainer runs the line of `tests/measure/embeddings/README.md`, writes the 20 searches
   (people's events, places, objects, seasons: as 0084 lists), ticks the relevant pictures, and
   sends back the JSON the pages download.
2. From that JSON: per model, the share of relevant pictures in the first 24, and the searches
   today's words answer as well; the seconds per photo on the maintainer's PC; the near-duplicate
   pairs found that the audit missed, judged.
3. Decision, written here: build (which model, for search, near duplicates, or both: then file the
   TODOs with their files), or not; and what becomes of 0084.

## Acceptance

- The measured table and the decision in this file; the follow-up TODOs filed, or 0084 and this
  one closed.

## Gain

To measure: the share of searches answered without Ollama, and the time per photo of a model on
the CPU against Ollama's 2 to 3.5 s on the GPU (measured 2026-10-10).

## Measured (2026-10-20, step 20 of mh-measure.ps1, maintainer's PC, 1,000 photos of C:\Photos, 4 CPUs)

Runs `measures-20261020-1350` and `-1406` (the second with searches rewritten as what is seen:
a model never knows who or where — names come from `people`, places from the GPS). 20 searches ×
2 models × 24 pictures judged by the maintainer (960 judgements, every box ticked first, the
misses unticked).

| | CLIP ViT-B/32 + multilingual text | SigLIP 2 base |
|---|---|---|
| relevant in the first 5 | 67 % | 69 % |
| relevant in the first 10 | 57 % | 61 % |
| relevant in the first 24 | 45 % | 48 % |
| share of the good photos found (15 searches with ≥ 5 good ones; good = union of both) | 75 % | 79 % |
| searches won (first 10) | 6 | 8 (6 tied) |
| seconds per photo (decode + model, 4 threads) | 0.057 | 0.104 |
| peak memory | 1.5 GB | 2.5 GB |
| model files | 0.9 GB | 1.5 GB |

- Strong on what is seen (a cat, a house front, a classroom, a beach, a cake: 4 or 5 of the
  first 5 right); weak on an action ("a girl dancing": 1 to 3 of 5). Five searches had 1 or 2
  good photos in the sample (kitchen, old man with a cap, Italian street, meerkats, kayak):
  not telling.
- Near duplicates (DINOv2, CLIP, SigLIP 2): the 50 closest pairs each, those the audit already
  calls near duplicates left out: **0 copy**; all bursts, retakes or alike scenes (the
  maintainer unticked every pair). Image embeddings add nothing to the audit's hashes for copies.
- Against Ollama's captions: 0.06–0.10 s per photo on the CPU, against 2–3.5 s on the GPU
  (measured 2026-10-10): 30 to 50 times faster, no GPU.

## Decision (maintainer, 2026-10-20)

- Build search by meaning with **CLIP** (multilingual text), opt-in: nearly SigLIP 2's
  precision (−2 to −4 points) at about half the time and memory → **0263**.
- No near duplicates by embeddings (0 copy found).
- 0084 (text vectors over Ollama's captions) closed UNNEEDED: search by image replaces it.
