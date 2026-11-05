# 0604 — Import chain: live follow and resume from a step

- **Priority**: Medium
- **Batch**: import
- **Depends**: 0481 (PARTIAL)
- **Files**: `mh.ps1`, `src/media_hygiene/review/import_steps_api.py`

## Why (review of feedback-2026-11-03-iterate (2026-11-05))

The chain after a phone import runs in `mh.ps1` on the host: the home page cannot follow it nor resume it. Decided: the chain writes its progress to a state file under `/cache` (e.g. `import-chain.json`: step, state, run), the home page follows it, and `mh.ps1` takes a "start from step N" argument. Windows PowerShell 5.1.
