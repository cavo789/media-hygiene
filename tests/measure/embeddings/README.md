# Image embeddings bench (TODO 0220, for 0221)

A measurement, never part of the published image: does "search by meaning" find the photos
a person expects, on your own photos and searches, and what does it cost per photo on the
CPU? Three models, ONNX exports run by the ONNX runtime already in the image:

| Model | For | Files | Licence (checked 2026-10-18) |
|---|---|---|---|
| SigLIP 2 base, patch 16, 224 px | searches + pairs | 1,536 MB (vision 372, text 1,130, tokenizer 34) | Apache-2.0 on Google's card; the ONNX export (onnx-community) states none: to check |
| CLIP ViT-B/32 + `clip-ViT-B-32-multilingual-v1` (text) | searches + pairs | 894 MB (vision 352, text 539, tokenizer 2, projection 1.6) | CLIP: MIT on OpenAI's GitHub repository, none on its Hugging Face card nor on the export (Xenova): to check; multilingual text: Apache-2.0 on its card |
| DINOv2 small | pairs only (no text) | 89 MB | Apache-2.0 on Meta's card; the export (onnx-community) states none: to check |

Sizes: Hugging Face API, read 2026-10-18; every file is pinned to one revision
(`models.py`). Full precision (fp32) everywhere: the bench measures the best each model can
do; a quantized variant (4× smaller) is a question for 0221 if one wins.

## Run it (Windows PowerShell 5.1)

Build or pull the image first (`docker build --tag media-hygiene .` on this branch). Then,
from any folder (`C:\temp` here):

```powershell
cd C:\temp
Invoke-WebRequest https://raw.githubusercontent.com/cavo789/media-hygiene/iterate/2026-10-17/tests/measure/mh-measure.ps1 -OutFile .\mh-measure.ps1
Unblock-File .\mh-measure.ps1
.\mh-measure.ps1 -Only 20 -Count 1 -Sample 1000 -Cpus 4 -Branch iterate/2026-10-17
```

The first run writes `%USERPROFILE%\media-hygiene\embeddings-queries.txt` with three
examples and stops: write your 20 searches there, in French, one per line (UTF-8), then run
the last line again. Step 20 downloads this folder from the branch, then runs, in one
`docker run`:

- `C:\Photos` mounted **read-only** at `/data/c/Photos` (where the audits saw it, so the
  index finds the same paths), the index volume `media-hygiene-cache` read-only at `/cache`;
- `tokenizers==0.23.2` (Apache-2.0, PyPI) installed into `/tmp` of the container, gone with it;
- the models downloaded **once** into `%USERPROFILE%\media-hygiene\embeddings-models`
  (2.5 GB, reused by the next runs; delete the folder to get the room back);
- `-Sample` photos drawn at random (fixed seed: the same photos at each run), each model in a
  process of its own with `-Cpus` threads (`docker run --cpus` set to the same number).

Without the script, the same run (the bench files in `C:\temp\embeddings`):

```powershell
docker run --rm --cpus 4 --mount "type=bind,source=C:\Photos,target=/data/c/Photos,readonly" --mount "type=volume,source=media-hygiene-cache,target=/cache,readonly" --mount "type=bind,source=C:\temp\embeddings,target=/bench/embeddings,readonly" -v "$HOME\media-hygiene\embeddings-models:/models" -v "$HOME\media-hygiene\embeddings-out:/out" --entrypoint sh media-hygiene -c "/usr/local/bin/python3 -m pip install -q --no-cache-dir --target /tmp/wheels tokenizers==0.23.2 && PYTHONPATH=/tmp/wheels:/bench python -m embeddings.measure --photos /data/c/Photos --queries /out/queries.txt --models-dir /models --out /out --count 1000 --cpus 4"
```

(`queries.txt` copied into `embeddings-out` first.)

## How long

Estimated for 1,000 photos on 4 CPUs, from the smoke run (below) and the models' sizes:
the download once (2.5 GB: 5 to 20 minutes depending on the connection), then about
10 minutes: DINOv2 0.06 s per photo measured, CLIP ViT-B/32 of the same order (fewer
patches, more layers), SigLIP 2 about 4 times DINOv2-small's work per photo (estimated
from their vision files: 372 MB against 89 MB); plus decoding each photo once per model and once for the audit's
hashes. Then the pages to judge (20 searches × 2 models × 24 pictures): every box starts
ticked, untick the misses.

## What it writes

`%USERPROFILE%\media-hygiene\embeddings-<date>\`:

- `index.html`: per model, seconds per photo (model, decoding), seconds per search, loading
  time, threads, RAM peak (the process's maximum resident size), files size, licence;
- `queries.html`: per search, the 24 best photos of each model side by side, and today's
  `search` answers among the same photos when the index has words (`tags` ran); every
  picture starts ticked **relevant**: untick those a person would not expect, then
  **Download the ticks (JSON)**;
- `pairs.html`: per model, the 50 closest pairs the audit does not already call near
  duplicates (its dHash and pHash test); every pair starts ticked **same photo**: untick
  those where neither is a copy of the other (crop, filter, mirror, edit), then download;
- `thumbs/`: the thumbnails the pages show. Your photos are only read.

A model sees what is in the picture, never who or where: write the searches as what can be
seen ("a woman in a kitchen", not a first name; "a house front", not a village). Names and
places come from `people` and the GPS (`places`): the product would combine them with the
model's part, which is what this bench measures.

The ticks stay in the browser while you work (local storage), but only the downloaded JSON
files count: send both to Claude (0221).

## Smoke run (devcontainer, 2026-10-18)

21 synthetic pictures (640 × 480 JPEG, coloured ellipses, one exact copy), `--cpus 2`, in the
project's image: DINOv2-small measured **0.057 s per photo**, RAM peak 246 MB, 89 MB of
files; the tokenizers of both text models checked (SigLIP 2: lowercase, `<eos>`, padded to
64 tokens; multilingual CLIP: `[CLS] … [SEP]`) and the CLIP projection read (512 × 768).
SigLIP 2 and CLIP themselves (2026-10-19, same 21 pictures and 3 French searches, devcontainer
venv, `--cpus 2`, `nice`): downloads pinned as in `models.py` (2.3 GB on disk), no failure,
pages written. Measured per photo: SigLIP 2 **0.12 s** (model), 0.04 s per search, loaded in
2.0 s, RAM peak **2.5 GB**; CLIP **0.039 s**, 0.007 s per search, 0.9 s, RAM peak 1.4 GB.
One model runs at a time, so the container needs about 2.5 GB of memory.

## Code

`measure.py` (command line), `runs.py` (sampling, one model's run, timings), `embedders.py`
(preprocessing, ONNX, tokenizers; a stub for the tests), `models.py` (files, revisions,
licences), `ranking.py` (best pictures, pairs, today's search), `pages.py` + `templates/`.
Tests: `tests/unit/test_embeddings_measure.py` (stub model, synthetic pictures, no download).
