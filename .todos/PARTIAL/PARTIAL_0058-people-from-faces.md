# 0058 — People: find faces, group them, let the user name them

- **Priority**: Low — design first; measure on the real collection before building anything
- **Batch**: people
- **Depends**: —
- **Files**: `src/media_hygiene/faces/` (new: detect, embed, cluster, models download), `src/media_hygiene/index/schema.py`, `src/media_hygiene/index/` (new `face_rows.py`), `src/media_hygiene/scan/file_check.py`, `src/media_hygiene/people/` (new: naming page, served like `places`), `src/media_hygiene/cli/` (new `cmd_people.py`), `src/media_hygiene/classify/rules/`, `src/media_hygiene/config/settings.py`, `src/media_hygiene/config/templates/config.toml.j2`, `src/media_hygiene/report/`, `pyproject.toml`, `Dockerfile`, `documentation/en/sort/`, `documentation/fr/sort/`

## Context

The maintainer asked (2026-10-10) whether the local Ollama could tag people in photos.

**Not with the vision model alone.** `qwen3.8:27b` (0029) describes a scene: how many people,
child or adult, selfie, group, portrait. It cannot say *who* someone is: it has never seen the
family. Asking it "same person on these two photos?" is slow (≈ 3.5 s per photo) and
unreliable, and such models often refuse to identify real people. The Ollama embedding models
on the machine (`bge-m3`, `mxbai-embed-large`) embed text, not faces.

Tagging people is a classic pipeline that needs no LLM:

1. **Detect** faces (a box and five landmarks per face).
2. **Embed** each aligned face as a vector: close vectors are probably the same person.
3. **Cluster** the vectors into unnamed groups.
4. **Name** the groups in the browser ("this group is Mamie"); a new face close to a named
   group gets the name, as a suggestion until confirmed.

### Overlap with Immich (0009)

0009 concluded the tool should not grow what Immich already does well, and faces are one of
those things. **Decide first** which question this answers:
- *find* photos of someone → Immich's job, do not build this;
- *file* photos by who is in them (`classify` / `sort`: "events with Mamie", a folder per
  child) → our job, build this.

Record the decision here before any code.

## Proposal

- **Models: OpenCV Zoo YuNet (detection, MIT) + SFace (embedding, Apache 2.0)**, ONNX,
  run with `onnxruntime` on CPU (amd64 and arm64 wheels). Tens of milliseconds per photo
  expected (to measure). Licences fit a public Docker Hub image.
  - **Not** InsightFace's pretrained models (ArcFace / `buffalo_l`): better, but licensed for
    non-commercial research only.
  - `opencv-python-headless` also ships both (`FaceDetectorYN`, `FaceRecognizerSF`) but is
    much heavier than `onnxruntime`; compare image sizes with `dive` before choosing.
  - Model files: downloaded once into `/cache` with a pinned SHA-256 (never under `/config`),
    or vendored if small enough (YuNet ≈ 230 KB; SFace ≈ 37 MB is not).
- **In the scan, opt-in**: `[people] enabled = false` by default. When on, the same decode
  that yields `VisualFacts` runs detection + embedding in the process pool; incremental like
  every other fact.
  - Skip faces smaller than `min_face` pixels and blurry ones (Laplacian sharpness already
    exists): they produce wrong groups.
  - Videos: later, on the keyframes of `video_prints`, if at all.
- **Index**: schema 6, a `faces` table keyed by the file identity (path, size, mtime) + model
  version: box, landmarks, detection score, embedding (float32 blob, 128 values). Pruned and
  moved with the file like the other rows.
- **Clustering**: cosine distance, threshold from SFace's documented value then tuned on the
  measurement below. Start with a simple pure-numpy approach (connected components / Chinese
  whispers over a nearest-neighbour graph); add a dependency only if the measurement asks
  for it. Groups recomputed from the index in seconds, never stored as truth.
- **Names**:
  - stored in `config.toml` as `[[people]]` (`name`, the reference face ids the user
    confirmed), written with tomlkit like `[[classify.places]]`; read back from disk and shown
    after each save (proof, not promise);
  - a face is assigned by its distance to the confirmed references of each person, so a
    re-cluster never loses a name.
- **`media-hygiene people`**: a browser page served like `review` / `places` (loopback
  `Host`, JSON-only `POST`), keyboard driven:
  - largest unnamed group first, a grid of face crops;
  - type a name, merge two groups, remove a wrong face from a group, "ignore" (strangers,
    posters, statues);
  - children who grow up: allow several reference sets per person.
- **Uses**:
  - the names go into the label layer of 0072 (`source = person`): searchable with the other
    words (0073, "Mamie plage") and written to XMP sidecars by 0074 (`PersonInImage`);
  - a `match = "person"` rule in `classify` ("events where X appears" → a category or folder);
  - a "people" column in `inventory.xlsx` / `.csv` and in the classify workbook;
- **Privacy**: face vectors are biometric data (GDPR art. 9).
  - they stay in `/cache`, never sent anywhere, never in reports beyond the names;
  - `people forget` deletes every face row and the `[[people]]` entries;
  - the docs say it plainly; the CLI says it in one line when the feature is turned on.
- **Ollama stays for scenes** (0029). It can add "group photo" / "portrait" / "child" tags,
  never identities.

## Measurement first (next session)

Run read-only on the maintainer's collection (`--mount …,readonly`, `--network none`, see the
memory note on local photos), on a sample of about 2,000 photos from varied years:
- [ ] seconds per photo for detection + embedding, on half the CPUs;
- [ ] faces found per photo, share of tiny or blurry faces skipped;
- [ ] group quality at two or three thresholds: how many groups are one person, how many mix
      two people (especially siblings and children across years);
- [ ] image size added by `onnxruntime` vs `opencv-python-headless`.

Note the figures here, then decide to build, reduce or drop.

## Acceptance

- [ ] Immich-overlap decision recorded in this file.
- [ ] Measurement above noted in this file.
- [ ] Synthetic faces only in tests and screenshots (`tests/support/docs/`: drawn or
      generated faces, never real photos).
- [ ] Off by default; turning it on never slows an audit that does not ask for it.
- [ ] Documentation en + fr (a sorting step, privacy, forget); `.po` translated.

## Status — PARTIAL (2026-10-11)

### Decisions recorded
- **Immich overlap (0009)**: build this to *file* photos by who is in them (`classify` /
  `sort`), not to *find* someone's photos (Immich's job). Said in
  `documentation/*/reference-people.md`.
- **Runtime**: `onnxruntime` (main dependency, locked at 1.30.0; MIT; cp314 amd64 + arm64
  wheels; no sympy since 1.25). Measured in a venv: 63 MB installed vs 153 MB for
  `opencv-python-headless`. The image needs nothing more (`libstdc++` is already required by
  `rawpy`). A `dive` measurement of the rebuilt image is still to do.
- **Models**: YuNet 2023mar + SFace 2021dec from OpenCV Zoo at pinned commits, SHA-256 pinned
  in `faces/weights.py`, downloaded at first use into `/cache/models`; never in the repo.
- Checked outside the repo against OpenCV's own `FaceDetectorYN` / `FaceRecognizerSF`: same
  boxes; alignment + embedding equal to 0.9998 cosine. About 30 ms per 512 px photo for
  detection + embedding, one thread, decoding excluded.

### Done
- `faces/`: letterbox + YuNet decoding + NMS (numpy), 5-point similarity alignment (PIL),
  `FaceEngine` behind a `Runner` seam, ONNX runner (lazy import, one thread), model download
  with checksum, worker (finder built once per process), clustering (30-NN graph above the
  threshold + Chinese whispers, fixed seed, blockwise).
- Index schema 8: `face_scans` + `faces` (box, landmarks, score, sharpness, float32 vector),
  per file version and model pair; pruned and moved with the file; `--forget` deletes all with
  `secure_delete` and reads back.
- `media-hygiene people` (read-only, page command): analyse what the cache lacks (half the
  CPUs, Ctrl+C keeps progress), group, summary, local read-only page of the groups (face crops
  cut on request, never written); `--sample N`, `--path`, `--forget`, `--port`.
- `[people]` settings: `similarity`, `min_face`, `min_sharpness` (applied at grouping time:
  changing them analyses nothing again).
- `status` line; `safety` sets (launcher publishes the port, mounts photos `:ro`).
- Docs en + fr: `reference-people.md` (privacy, forget, measure first), command reference,
  documentation indexes; `.po` translated.
- Tests: synthetic tensors and a fake finder only (`tests/support/faces.py`); no model
  download, no real face.

### Not done
- Measurement on the real collection (seconds per photo, faces per photo, share skipped,
  group quality at 2–3 thresholds, image size with `dive`).
  **Reason:** no Docker and no access to the photos during the night run; `people --sample`
  is the tool for it. Then tune `similarity` / `min_face` / `min_sharpness` defaults and
  replace the illustrative figures of the docs example.
- Naming: `[[people]]` in `config.toml` (tomlkit, read back), reference faces per person
  (several sets for children), assignment by distance to references; page actions (type a
  name, merge groups, remove a wrong face, ignore).
  **Reason:** scope — first slice is find + group + show; naming needs the measurement first
  to know what the groups look like.
  **Follow-up:** 0091 (naming + `search` by person).
- Uses of the names: label layer `source = person` (0072), `search` (0073), XMP
  `PersonInImage` (0074), `match = "person"` classify rule, a column in `inventory` and in the
  classify workbook; a sorting step in `documentation/*/sort/`.
  **Reason:** depend on naming.
- Opt-in face finding inside the audit scan (`[people] enabled`).
  **Reason:** deliberately left out: `people` analyses on its own, so an audit is never slowed;
  revisit once the cost per photo is measured.
- Videos (keyframes of `video_prints`); tiling for small faces in large group photos (YuNet's
  ONNX input is a fixed 640 x 640 letterbox).
  **Reason:** wait for the measurement.
- Synthetic faces for documentation screenshots (`tests/support/docs/`) and the captures
  (`help.txt`, `config.txt`, `config.toml`).
  **Reason:** no `docs_screenshots` run tonight.

### Follow-ups delivered (2026-10-11, third pass)
- Naming on the page (`[[people.person]]`, merge, remove a face, ignore, suggestions) and
  `search` by person (`TagSource.PERSON`): **0091** (DONE).
- Face finding inside the audit, on request (`audit --people`, `[people] with_audit`):
  **0089** (DONE).
- The `match = "person"` classify rule: filed as **0095**; the sort step waits for it
  (**0088**, BLOCKED). ArcFace as a choice: **0090**, BLOCKED until measured.

## Inbox (2026-10-14)

- The measurement is now step 6c (`people --sample 200` on `C:\Photos`): seconds per photo, faces, share left out; the group quality and `dive` stay by hand of `tests/measure/mh-measure.ps1`.

## Windows measurement (2026-10-14)

Measured by the maintainer on 2026-10-14 with `tests/measure/mh-measure.ps1` (Windows, Docker
Desktop, image built from `main`; run `measures-20261014-2133`, test folder of 2,000 photos
copied twice). `people --sample 200` on `C:\Photos` (52,054 files): 200 photos analysed, 96 faces
(0.48 per photo), 0.16 s per photo; the tool's estimate for a full run: 50,323 more photos,
about 16 min 20 s. Wall time of the sample: 12.6 s. Still waiting: the group quality at 2–3
thresholds (the maintainer's eyes on the page) and the image size with `dive`.
