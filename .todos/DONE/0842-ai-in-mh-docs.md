# 0842 — The documentation says what is built in and what needs a local AI (and how much VRAM)

- **Priority**: Medium
- **Batch**: docs
- **Depends**: none
- **Files**: `documentation/en/reference-ai.md`, `documentation/fr/reference-ai.md`, `documentation/en/commands/people.md`, `documentation/fr/commands/people.md`, `documentation/en/commands/tags.md`, `documentation/fr/commands/tags.md`, `documentation/en/commands/classify.md`, `documentation/fr/commands/classify.md`, `documentation/en/commands/spots.md`, `documentation/fr/commands/spots.md`, `documentation/en/commands/library.md`, `documentation/fr/commands/library.md`, `documentation/en/commands/places.md`, `documentation/fr/commands/places.md`, `.config/mkdocs/mkdocs.yml`, `src/media_hygiene/cli/`

## Why (maintainer, 2026-11-15)

Users ask "do I need a local AI?". The answer (no, except three optional features) is
nowhere in one sentence. Someone reading `people`, `places`, `library`… must see at once
what is **built in** (runs on the processor, no graphics card, nothing to install) and
what needs **a local AI** (Ollama), with the VRAM it takes: some users have 2 or 4 GB.
🤖 is used both for "needs Ollama" and for built-in models (`tags --meaning`, the turn
guess on `people.md`), which misleads.

## What exists (checked 2026-11-15)

| Feature | Model | Needs |
|---|---|---|
| Faces: `people`, `/person`, turn guess | YuNet + SFace, ONNX, ~39 MB downloaded once | Built in, CPU |
| Search by meaning: `tags --meaning` | CLIP image/text, CPU | Built in, CPU |
| Describe photos: `tags`, `classify` subjects, `spots --vision` | a vision model in Ollama (`[classify.ai] model`) | Ollama, optional |
| Duplicates, broken, blur, bursts, near duplicates, places, towns, landmarks (GeoNames) | none: hashes, measures, offline data | Nothing |

## To do

1. `reference-ai.md` (EN + FR, `nav` of mkdocs, `test_docs_site.py`): first sentence
   "mh works without any AI to install; three optional features ask a local model
   (Ollama)"; the table above, with for each: what is downloaded, where it runs, what
   leaves the machine (nothing), RAM/VRAM.
2. On each command page, one line near the top (the "At a glance" table): **Built in** or
   **🤖 Needs a local AI (Ollama)**, linking to `reference-ai.md`.
3. 🤖 only for "needs Ollama", in the docs and in the CLI help panels / menu catalog;
   reword the built-in mentions (`tags --meaning`, `people.md` turn guess).
4. VRAM: a table of vision models that fit 2 / 4 / 8 GB, the one mh suggests per size,
   and what happens without a GPU (Ollama on CPU: works, much slower). **Measure** what
   can be measured on the maintainer's machine (`ollama ps` size of the configured model,
   seconds per photo) and **check** the other sizes against Ollama's library pages before
   writing them: no figure from memory (rule: a fact about a third-party product is checked).
5. `people.md` "Your privacy": one line "no Ollama, no graphics card" + link.

## Done (2026-11-27)

- `reference-ai.md` EN + FR (nav, README contents): the one sentence, the table, the VRAM table.
- "Local AI" / "IA locale" row in the At a glance table of people, tags, classify, spots,
  library, places; 🤖 removed from the built-in mentions (`tags --meaning`, the turn guess);
  people "Your privacy" line.
- CLI: already right (`--meaning` outside the 🤖 panel; only `tags` has `ai=True` in the menu).
- Measured (devcontainer → host Ollama, 6 synthetic 768×576 JPEG, `/api/generate`, 80 tokens
  max): `qwen3.8:27b` Q4_K_M 17.4 GB VRAM (`/api/ps`), cold 10.9 s, warm 1.6–2.3 s per photo.
  Checked: model sizes on ollama.com/library/<model>/tags (2026-11-27).
- Left: no measurement of a small model nor of CPU-only speed (not pulled on the maintainer's
  machine); the suggested models per size are a choice, not measured quality.
