# 0029 — `classify` asks a local vision model (Ollama) about loose photos

- **Priority**: Medium — the main category source for photos in date-only folders, once 0026–0028 and 0035 work without it
- **Batch**: ai
- **Depends**: 0026, 0035
- **Files**: `src/media_hygiene/classify/ai/` (new: client, describe, mapping, sampling), `src/media_hygiene/index/schema.py`, `src/media_hygiene/index/repository.py`, `src/media_hygiene/config/settings.py`, `src/media_hygiene/config/templates/config.toml.j2`, `src/media_hygiene/cli/cmd_classify.py`, `documentation/en/`, `documentation/fr/`

## Context

Folder names, dates (0026) and the calendar (0035) sort much of a family collection. Photos in
date-only folders (`Juillet 2016`, `2019-04`, `DCIM`) still need a subject: beach, school
show, pets, works at home, documents. A local vision model can provide it without any photo
leaving the machine.

### Benchmark (2026-09-28)

- **Setup**: `qwen3.8:27b-mtp-q4_K_M` on Ollama 0.34.3, on the maintainer's GPU.
- **Sample**: 12 photos of a real collection, from 12 different folders, sent at 768 px.
- **Call settings**: `think: false`, temperature 0, JSON-schema output.

| Step | Time |
|---|---|
| Model load (first call only) | 8.2 s |
| Describe one photo (≈ 476 prompt tokens, ≈ 120 output tokens at ≈ 48 tok/s) | ≈ 3.5 s |
| Map the description to a category (text only) | ≈ 0.9 s |

At about 4.4 s per photo, 65,000 photos would take about 80 hours. **Every photo cannot go
through the model.**

Quality:
- Descriptions were accurate and useful. Good mappings: a construction site → Home and works;
  a school choir → School; an empty flat → Home.
- **Occasions were missed**: nothing on a Saint-Nicolas photo nor on a Christmas Eve photo.
  The folder name (0026) and the calendar (0035) knew.
- **The `kind` field is unreliable**: two outdoor sculptures were tagged "screenshot", and one
  was mapped to "School". Screenshots and documents must come from metadata (0035), not from
  the model.
- **A "Family and portraits" category swallows everything**: 7 of 12 photos.
- **A 120 px thumbnail produced an invented, detailed document title.** Tiny images must be
  skipped.

## Proposal

- **Only ask where stronger signals are silent**: skip the files already decided by
  `existing_folder`, `event_neighbour` (0026), `calendar`, `date_range`, `path`, `camera` or
  `kind` (0035), and images below a minimum size. The answer feeds the `subject` rule kind of
  0035.
- **Event sampling**: `samples_per_event` representatives per event, the sharpest (sharpness
  is in the index) spread across the event's span. The other photos and the videos inherit.
  **Stable choice**: when a setting recuts the events, the photos already described are
  preferred as samples, so a new cut does not cost a new night.
  A `subject` rule can ask for per-photo evaluation (`per_photo = true`), and the console then
  shows the time estimate first.
- **Two steps**, so that changing the taxonomy costs seconds, not a night:
  1. **Describe** (vision): a short description and tags, independent of the taxonomy. Cached
     in the index, keyed by the file identity + model + prompt version. Resumable after Ctrl+C.
     Keep the output short: output tokens dominate the time.
  2. **Map** (text only): descriptions → categories of the current taxonomy, with a JSON-schema
     `enum`. Batch many descriptions per call. Compare with `bge-m3` embeddings (milliseconds,
     already on the machine).
- **Confidence** = agreement among the event's samples (3 of 3 → high; 1 of 3 → to check),
  never a percentage the model states about itself.
- **Client**:
  - standard library `urllib` in `asyncio.to_thread` (no new dependency);
  - one request at a time by default (a single GPU), configurable;
  - timeouts and retries;
  - at start, `/api/show` must list the `vision` capability, otherwise a clear error names the
    model;
  - images sent as 768 px JPEG, made in the process pool (`report/thumbnails.py`,
    `raw_preview` for RAW).
- **Config** `[classify.ai]`: `url`, `model`, `samples_per_event`, `min_edge`, `concurrency`,
  prompts in `templates/`.
- **`classify --sample N`**: describes N random loose photos and prints seconds per photo and
  the estimated total, before committing to a long run.
- **A long run is never a surprise, and never in the way**:
  - before describing, `classify` prints the number of photos to describe and the estimated
    time, and asks for confirmation above `[classify.ai] confirm_above` photos (`--yes`);
  - a run describes only the samples missing from the cache; Ctrl+C keeps what is done;
  - `--no-describe` uses the cache only (seconds): the user iterates on the rules and the
    taxonomy without waiting, the undescribed events stay to the other rules.
- **Docker networking**:
  - Docker Desktop resolves `host.docker.internal`;
  - Docker Engine on Linux or WSL needs `--add-host=host.docker.internal:host-gateway`, with
    Ollama listening beyond loopback (`OLLAMA_HOST`).
  - Document both, and warn that images go to the configured URL.
- **Kept for later, not built here (2026-09-29): a fast CLIP pass.** If `--sample` shows
  events mixing several subjects, or a total time too long, evaluate CLIP: images and sentences
  turned into comparable vectors, so that *every* photo is scored against the categories
  written as sentences ("a beach", "a school show"). It runs on CPU with onnxruntime, in the
  order of tens of milliseconds per photo (to measure), its model downloaded once into
  `/cache`; Ollama would then describe only the samples. Limits: it sees scenes, not
  occasions, and [sorta](https://github.com/shinKatana0/sorta) measured 59 % precision on its
  CLIP "screenshot" class. It would also allow a search by words (albums of 0041).

## Acceptance

- [ ] Fake Ollama server (asyncio) in tests: describe, map, cache hit, resume after
      interruption, missing `vision` capability refused.
- [ ] `--sample 50` on the maintainer's collection: time per photo and mapping accuracy noted in
      this file before closing.
- [ ] Documentation en + fr (networking, privacy, time estimate); `.po` translated.

## Status — PARTIAL (2026-10-02)

### Done
- `match = "subject"` rule (`categories`, optional `per_photo`), opt-in: nothing is sent
  without a `subject` rule and `[classify.ai] model`; a rule without a model stops with a
  clear error. Default rules unchanged.
- Only files no stronger rule decided are asked about (`classify/ai/sampling.py`: silent
  reasons no-signal, date-only, other-category, previous-guess; stay and undated skipped);
  photos below `min_edge` (shorter side) and videos are never sent, they follow their event.
- Event sampling: `samples_per_event` samples, the sharpest of each part of the event's span;
  already-described photos preferred (a recut costs no new description). Lone files are
  their own unit.
- Two steps: describe (vision, JSON schema, `think: false`, temperature 0, short output,
  768 px JPEG from the process pool via `report/thumbnails.jpeg_preview`, RAW previews
  included), cached in the index (schema 4, `descriptions` table keyed by path + size + mtime
  + model + prompt digest; follows `sort` moves, forgotten with the file); map (text only,
  batched by `batch_size`, JSON-schema `enum` + "none", unusable batch retried one by one,
  cached in `subject_mappings`).
- Confidence = agreement of samples: unanimous with 2+ samples → rule score (85, sure);
  otherwise capped at `unsure` (to check); "none" winning → no subject.
- Client: `urllib` in `asyncio.to_thread`, retries on timeouts/5xx, `/api/show` must list
  `vision`, clear errors (unknown model → `ollama pull`, unreachable → `--add-host` tip).
- `[classify.ai]`: url, model, map_model, samples_per_event, min_edge, image_edge,
  concurrency, timeout_seconds, retries, batch_size, confirm_above, seconds_per_photo;
  overridable with one JSON env var `MEDIA_HYGIENE_CLASSIFY__AI`. Prompts in
  `classify/ai/templates/`.
- `classify --sample N` (table, seconds per photo, estimate of the full run),
  `--no-describe` (cache only), `--yes`; estimate printed before describing, confirmation
  above `confirm_above` (refused or no terminal → cache only); Ctrl+C stops between photos,
  the next run resumes.
- Tests with a fake asyncio Ollama server: describe, map, cache hit, resume after
  interruption, missing `vision` refused, nonsense answers, server error, batch fallback,
  no model, no /cache, per_photo.
- Docs en + fr: new sorting step 8 (networking, privacy, time estimate), rule tables of
  step 6, reference pages; `.po` translated.
- Real-model smoke test against the local Ollama (qwen3.8 27B) on synthetic drawn images
  only: `--sample 3`, full run, `--no-describe` and the error paths work; ≈ 1.9 s per
  synthetic photo once the model is loaded (not representative of real photos).

### Not done
- `--sample 50` on the maintainer's collection: time per photo and mapping accuracy noted in
  this file.
  **Reason:** the run that implemented this was not allowed to read the maintainer's real
  photos; the maintainer must run it and note the figures here before closing.
- `bge-m3` embeddings as a comparison or alternative to the mapping call: not built.
  **Reason:** the proposal says "compare with"; the mapping call alone is cached and batched.
  Worth measuring with the `--sample 50` run above before deciding.
- CLIP fast pass: explicitly kept for later by the proposal.
