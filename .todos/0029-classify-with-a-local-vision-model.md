# 0029 — `classify` asks a local vision model (Ollama) about loose photos

- **Priority**: Medium — the main category source for photos in date-only folders, once 0026–0028 and 0035 work without it
- **Batch**: ai
- **Depends**: 0026, 0035
- **Files**: `src/media_dedup/classify/ai/` (new: client, describe, mapping, sampling), `src/media_dedup/index/schema.py`, `src/media_dedup/index/repository.py`, `src/media_dedup/config/settings.py`, `src/media_dedup/config/templates/config.toml.j2`, `src/media_dedup/cli/cmd_classify.py`, `documentation/en/`, `documentation/fr/`

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

## Acceptance

- [ ] Fake Ollama server (asyncio) in tests: describe, map, cache hit, resume after
      interruption, missing `vision` capability refused.
- [ ] `--sample 50` on the maintainer's collection: time per photo and mapping accuracy noted in
      this file before closing.
- [ ] Documentation en + fr (networking, privacy, time estimate); `.po` translated.
