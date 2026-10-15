# 0166 — `people`: measure what `onnxruntime` adds to the image with `dive`

- **Priority**: Low
- **Batch**: people
- **Depends**: —
- **Files**: `.todos/DONE/DONE_0058-people-from-faces.md`, `documentation/en/reference-people.md`, `documentation/fr/reference-people.md`

## Context

Follows 0058 (closed DONE on 2026-10-15). `onnxruntime` became a main dependency for face
finding. Measured 2026-10-11 in a venv (not in the image): 63 MB installed, against 153 MB for
`opencv-python-headless`. The size it adds to the shipped image was never measured: the image
is what users download.

The other leftovers of 0058 are covered elsewhere: the group quality on the real collection by
0104 §5–6 (the maintainer's eyes on the page); the synthetic faces of the documentation by
`tests/support/docs/portraits.py` and `people_story.py` (`images/people.webp`). Videos and
tiling for small faces were dropped (inbox of 2026-10-15): measured 2026-10-14 on `C:\Photos`,
0.48 face per photo, 0.16 s per photo.

## What to do

1. `build`, then `dive_ci` / `dive` (`-j`): the size of the layer holding the venv, and
   `onnxruntime`'s share of it (`du` of its site-packages folder in the image).
2. Write the figures (measured, how, where) in this file and in the commit message.
3. If `onnxruntime` weighs more than ≈ 20 % of the image, file a TODO weighing an optional
   extra or a separate image tag; otherwise nothing more.

## Acceptance

- The size added by `onnxruntime` to the image, measured, written here.

## Decided (2026-10-15)

- The maintainer gives the go-ahead (`/todo:iterate` of 2026-10-15): build the image locally
  under `nice -n 19`, then `dive` and `du` in the image.

## Measured (2026-10-15)

Local build `docker build --target local` (`build` helper, `nice -n 19`), then
`docker image inspect`, `docker history` and `du -sk` run in the image (venv `/opt/venv`,
Python 3.14, onnxruntime 1.30.0). All figures measured; `dive -j` not needed (`docker history`
gives the per-layer sizes).

| What | Size | Share |
|---|---|---|
| Whole image | 411,073,474 B (411 MB, 392 MiB) | 100 % |
| Layer `COPY /opt/venv` | 236 MB (`du` of `/opt/venv`: 244,880 KiB) | 57 % of the image |
| `site-packages/onnxruntime` | 68,208 KiB (69.8 MB) | 17.0 % of the image, 27.9 % of the venv |
| + `.dist-info` (64 KiB) and `bin/onnxruntime_test` (4 KiB) | 68,276 KiB | 17.0 % |
| + deps pulled by it: `google` (protobuf) 2,728 KiB, `flatbuffers` 268 KiB | 71,272 KiB (73.0 MB) | 17.8 % |

- No shared library outside its folder (no `onnxruntime.libs`; `find` finds nothing else).
  `numpy` (43.6 MB + `numpy.libs` 26.8 MB) is needed without it.
- Below the 20 % threshold: no TODO filed for an optional extra or a separate image tag.
- Documentation: neither `reference-people.md` makes a claim on the image size; unchanged.

## Decided (2026-10-15)

- The maintainer accepts the 17 % (review of PR #7): `onnxruntime` stays in the image, no
  optional extra nor separate tag.
