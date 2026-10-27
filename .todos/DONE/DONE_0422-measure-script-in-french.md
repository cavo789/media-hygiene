# 0422 — `mh-measure.ps1`: steps 1–35 in French

- **Priority**: Low
- **Batch**: measure
- **Depends**: —
- **Files**: `tests/measure/mh-measure.ps1`

## Why

Leftover of 0366, decided by the maintainer (inbox, 2026-10-27): step 36 is in French, steps 1–35
(~230 questions and lines, estimated from a count in 0366) are still in English.

## What

Translate the questions and lines the maintainer reads; keep the file ASCII (`[char]` for
accents, as step 36), PowerShell 5.1; result keys and file names unchanged (they are read back
from the devcontainer). A test that the script stays ASCII if none exists.
