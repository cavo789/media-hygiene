# 0157 — `classify` reads the index in one pass, as `audit` does

- **Priority**: Low — two `SELECT`s and two row parses per file at each `classify` run: about a second for 52,000 files, several seconds for 300,000
- **Batch**: index
- **Depends**: —
- **Files**: `src/media_hygiene/services/classify.py`, `tests/integration/test_index_one_pass.py`

## Context

Speed and cache review of 2026-10-14 (third pass). The maintainer asked whether `classify` keeps
and reuses the cache. It does: after an audit nothing is decoded again, and the files moved by
`sort` keep their facts (`FactsRepository.move`). One gap: 0135 made the audit read the index
in one pass (`repository.preload(roots)` in `AuditService._analyse_files`), but
`ClassifyService._inputs` does not preload:

- `BrokenFileFinder.find` calls `repository.get(file)` for every file: one `SELECT` and one
  parse of the row (`rows.facts_of`, the metadata JSON through pydantic);
- then `media_input(file, root, repository)` calls `get` again for every file.

0135 measured ≈ 5 µs per `SELECT` and ≈ 4 µs per parse on the demo index, whose metadata is
shorter than real EXIF.

## What to do

1. `ClassifyService._inputs`: call `repository.preload(roots)` right after `forget_missing`, as
   the audit does. `get` then answers from memory, and `put` keeps it up to date.
2. Extend `tests/integration/test_index_one_pass.py`: a warm `classify` issues no per-file
   `SELECT` (statement tracer, as for the audit).

## Acceptance

- The test of item 2 passes; the `classify` tests pass unchanged.
