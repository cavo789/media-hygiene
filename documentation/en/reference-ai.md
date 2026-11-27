# Local AI

[Documentation](README.md) › Reference · 🇫🇷 [Français](../fr/reference-ai.md)

**media-hygiene works without any AI to install; three optional features ask a local model
(Ollama).** Everything else runs on your processor, with no graphics card and nothing sent.

In this documentation, 🤖 marks only what needs a local AI (Ollama). What is **built in** carries
no 🤖: it runs inside the image, on the processor.

## What needs what

| Feature | Model | Downloaded | Runs on | Leaves your computer | Needs |
|---|---|---|---|---|---|
| Duplicates, broken files, blur, bursts, near duplicates, places, towns, landmarks | none: hashes, measures, the GeoNames copy inside the image | nothing | the processor | nothing | **Built in** |
| Faces: [`people`](commands/people.md), `/person`, the turn guess | YuNet + SFace (ONNX) | 39 MB, once, into the cache | the processor | nothing | **Built in**, no graphics card |
| Search by meaning: [`tags --meaning`](commands/tags.md) | CLIP image/text | 894 MB, once, into the cache | the processor | nothing | **Built in**, no graphics card |
| 🤖 Describe photos: [`tags`](commands/tags.md), the `subject` rule of [`classify`](commands/classify.md), [`spots --vision`](commands/spots.md) | a vision model you choose in Ollama (`[classify.ai] model`) | by Ollama, its size below | your graphics card, or the processor | nothing: the photos go to `[classify.ai] url` only, keep it on your computer | **Ollama, optional** |

## 🤖 Which vision model for your graphics card

A model fits when its size is below your graphics card's memory (VRAM), with some room left.
Sizes are the download sizes shown on Ollama's library pages (checked 2026-11-27 on
`ollama.com/library/<model>/tags`); the memory used once loaded is close to it (measured: a
17.7 GB model used 17.4 GB in `ollama ps`).

| Graphics card memory | Vision models that fit (download size) | Suggested |
|---|---|---|
| 2 GB | `moondream:1.8b` (1.7 GB), `qwen3-vl:2b` (1.9 GB) | `qwen3-vl:2b` |
| 4 GB | `llava-phi3:3.8b` (2.9 GB), `qwen2.5vl:3b` (3.2 GB), `qwen3-vl:4b` (3.3 GB), `gemma3:4b` (3.4 GB) | `qwen3-vl:4b` |
| 8 GB | `qwen2.5vl:7b` (6.0 GB), `qwen3-vl:8b` (6.2 GB) | `qwen3-vl:8b` |
| 24 GB | `gemma3:27b` (17 GB), `qwen3-vl:32b` (21 GB) | `qwen3-vl:32b` |

The suggestion is the newest family of each size; the answers of the small models are less
precise. Measure yours before a full run: `tags --sample 20` prints the time per photo and the
estimate of the whole collection.

Measured on the maintainer's computer (24 GB graphics card, 2026-11-27, 6 synthetic 768×576
pictures, one sentence + 5 words each): a 27B vision model (`qwen3.8:27b`, Q4_K_M) used
17.4 GB of graphics memory, took 10.9 s for the first photo (loading the model) then 1.6 to
2.3 s per photo.

**Without a graphics card**, Ollama runs the model on the processor and in the computer's
memory (`ollama ps` then shows `100% CPU`): it works, much slower. Try a small model and
`--sample` first.

## Set it up

1. Install Ollama on your computer and pull a model, e.g. `ollama pull qwen3-vl:4b`.
2. In `config.toml`, `[classify.ai]`: `model = "qwen3-vl:4b"` (`url` is already your computer's).
3. `tags --sample 20` 🤖: the time per photo and the estimate.

Empty `model`: no photo is ever sent, and the three features are simply off.
