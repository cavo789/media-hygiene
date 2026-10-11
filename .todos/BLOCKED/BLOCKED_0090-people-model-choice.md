# 0090 — `people`: let the user choose a stronger face model (ArcFace), at their own licence risk

- **Priority**: Low — measure SFace on the real collection first (0058)
- **Batch**: people
- **Depends**: 0058
- **Files**: `src/media_hygiene/faces/weights.py`, `src/media_hygiene/faces/models.py`, `src/media_hygiene/faces/engine.py`, `src/media_hygiene/faces/detect.py`, `src/media_hygiene/faces/worker.py`, `src/media_hygiene/services/people.py`, `src/media_hygiene/config/people_settings.py`, `src/media_hygiene/config/templates/config.toml.j2`, `src/media_hygiene/console/people_view.py`, `documentation/en/reference-people.md`, `documentation/fr/reference-people.md`, `documentation/en/commands/people.md`, `documentation/fr/commands/people.md`, `tests/unit/test_faces_engine.py`, `tests/unit/test_faces_weights.py`

## Context

`people` uses YuNet (MIT) + SFace (Apache 2.0), downloaded on first use from OpenCV Zoo
(0058). OpenCV itself would not do better: it runs the same two models, and the night run
checked identical results. What would recognize better, mainly across ages and poses, is a
stronger recognition model, such as InsightFace's ArcFace (`buffalo_l`: SCRFD detector + ResNet-50
ArcFace, 512 values per face).

**Licence:** the InsightFace code is MIT, but its pretrained models are released for
non-commercial research only. The maintainer's use is private (review of 2026-10-11), but
this image is public: it must never ship, mirror or download these weights by default.

## Goal

- `[people] model = "sface"` (default) or `"arcface"` in `config.toml`, with a comment that
  says what the licence of each model allows.
- `"arcface"`: downloaded on first use from InsightFace's own release, SHA-256 pinned like the
  others, after one line saying the licence (non-commercial use only) and that choosing it is
  the user's decision. Never in the image, never in the repository.
- The engine seam (`Runner`, `FaceEngine`) takes a detector + embedder pair per model: SCRFD's
  decoding next to YuNet's; 512 values instead of 128; its own similarity default.
- The faces are already stored per model (`faces`, key (path, model)): changing the model
  analyses again, without forgetting the faces of the other model. `--forget` forgets all models.
  Say it before the analysis starts ("another model: every photo is looked at again").

## Before building

Measure first: same photos (`people --path` on one year), SFace then ArcFace, count the groups
that mix two people and the people split into several groups. Build only if ArcFace is clearly
better on the maintainer's photos.

## Acceptance

- The default stays SFace; nothing is downloaded from InsightFace unless the user asks.
- Both models work on the same index; switching back reuses the faces already found.
- Docs (en + fr) explain the choice and the licence in plain words.

## Status — BLOCKED (2026-10-11)

### Not done
- All items remain open.
  **Reason:** the TODO asks to measure SFace against ArcFace on the maintainer's photos
  before building, and to build only if ArcFace is clearly better. The night run has no
  access to the photos, and must never download InsightFace weights (non-commercial
  licence). Unblocks with the maintainer's measurement: `people --path "C:\Photos\2023"`
  (SFace page), then the private script
  `.claude/plans/night-2026-10-10/0090-arcface-measure.py` (git-ignored, run in a throwaway
  venv, downloads buffalo_l into `~/.insightface` on the maintainer's explicit run only) on
  the same folder; count on each page the groups mixing two people, the people split into
  several groups, and the faces left alone. Record the figures here, then build or drop.
