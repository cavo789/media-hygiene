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
