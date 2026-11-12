# 0717 — One run of `docs_screenshots` for the captures the PARTIAL TODOs left stale

- **Priority**: Low
- **Batch**: docs
- **Depends**: —
- **Files**: `documentation/en/`, `documentation/fr/`, `tests/support/docs/`

Filed by `/todo:inbox` on 2026-11-12: 35 items of the PARTIAL TODOs only waited for the
captures to be made again; they now point here, so the inbox asks once instead of 35 times.

## What to do

Run `docs_screenshots` (then `docs_screenshots fr`), check the diff of the captures and the
`<!-- capture: … -->` console blocks, commit them.

TODOs whose captures changed: 0339, 0349, 0430, 0431, 0432, 0448, 0463, 0492, 0498, 0505, 0510, 0514, 0534, 0543, 0545, 0550, 0567, 0572, 0655, 0657, 0661, 0664, 0665, 0667, 0683, 0687, 0689, 0690, 0694; also the console output of `audit` (its last
step, the thumbnails, 0674).

## Acceptance

- Every capture and console block regenerated; `tests/unit/test_documentation.py` passes
  (no unused screenshot).

## Decided (2026-11-12)

The maintainer gave the go in `/todo:iterate` of 2026-11-12: run `docs_screenshots` then
`docs_screenshots fr` once, at the **end** of that run (after its last lot, so the captures
its own lots make stale are refreshed too), committed on its own on the run branch.
