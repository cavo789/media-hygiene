# 0083 — Tags follow-ups: near-duplicate inheritance, videos, classify reusing the vision tags

- **Priority**: Low
- **Batch**: tags
- **Depends**: 0082
- **Files**: `src/media_hygiene/tags/selection.py`, `src/media_hygiene/tags/vision.py`, `src/media_hygiene/services/tag_describe.py`, `src/media_hygiene/classify/ai/describe.py`, `src/media_hygiene/classify/ai/subjects.py`, `tests/integration/tags/`

## Context

TODO 0072 (closed) delivered `media-hygiene tags`. It describes one photo per set of identical
files (SHA-256) and per burst series (`plan.bursts`, the sharpest shot); the others inherit its
`vision` and `caption` tags (`tags/selection.vision_plan`). Three parts were left out:

1. **Near-duplicate groups** (`plan/near`, `near_video`) do not share a description: a
   WhatsApp copy and its original are each sent to the model. The near search is heavier
   (multi-index hashing over the whole index) and its groups depend on `review --near`
   decisions.
2. **Videos** are never described: one keyframe of `video_prints` (already decoded by the
   audit) could answer for the video.
3. **`classify`** describes the photos again with its own question (`subject` rule) instead of
   reading the `vision` tags already in the index.

The 2026-10-10 benchmark estimates ≈ 30 h of model time for ≈ 50,000 photos: every photo not
sent counts.

## Steps

- [ ] Measure the cost of the near-duplicate search on the real collection (time, memory) when
  `tags` runs it from the index alone; decide whether `tags` runs it or reads the groups of the
  last audit report.
- [ ] Near groups: the kept version answers for its copies (as the sharpest shot does in a
  burst); a copy whose group a `review --near` decision dissolved keeps its own description.
- [ ] Videos: describe one keyframe (middle of `video_prints`), stored under the video's path;
  respect `min_edge` on the frame size.
- [ ] `classify` `subject` rule: when the photo has `vision` tags of the current model, map
  them to the categories without a new description; describe only the others. Keep the
  existing `describe.txt` path for the categories' wording if the mapping needs it.
- [ ] Integration tests with the fake Ollama: a near copy not sent, a video described once,
  `classify` sending nothing when tags exist.
- [ ] Docs en/fr `reference-tags.md` (what is described, what inherits).

## Acceptance

- On a tree with a near-duplicate pair, a video and a classified folder, `tags` then
  `classify` send each picture to the model at most once.
