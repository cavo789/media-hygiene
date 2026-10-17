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
