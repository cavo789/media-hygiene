# 0135 — Read the index in one pass per audit, and open it once

- **Priority**: Medium — a few seconds per audit on 70,000 files, to be confirmed by 0131
- **Batch**: index
- **Depends**: 0131
- **Files**: `src/media_hygiene/index/repository.py`, `src/media_hygiene/index/rows.py`, `src/media_hygiene/index/schema.py`, `src/media_hygiene/scan/broken.py`, `src/media_hygiene/scan/exact.py`, `src/media_hygiene/scan/file_check.py`, `src/media_hygiene/services/audit.py`, `src/media_hygiene/services/listing.py`

## Context

Speed review of 2026-10-14. Measured in the devcontainer, one `FactsRepository.get` costs about
5 µs for the `SELECT` plus 4 µs for `rows.facts_of`, which parses the metadata JSON with pydantic.
The demo index has short metadata; real EXIF is longer and costs more. Call sites per audit:

- `scan/broken.py`: one `get` per file (integrity pass);
- `scan/exact.py`: `get` per size-collision candidate, then `get` again in `put(file,
  step.store(repository.get(file), …))`, for the partial and again for the full digest;
- `scan/file_check.py`: `get` again for the files that need a check.

Each `get` rebuilds the whole `FileFacts`, metadata included, even when only a digest is needed.

`FactsRepository.open` runs `schema.prepare` on every open: a dozen `CREATE TABLE IF NOT EXISTS`,
`PRAGMA table_info` and a `PRAGMA user_version` write. An audit opens the index 3 times (listing
read, listing save, analysis).

## What to do

1. `FactsRepository.load_under(roots)`: one `SELECT` of the rows below the roots into a
   dict path → row. `get` reads the dict, and the dict is updated by `put`.
2. Parse the metadata lazily: keep the JSON text in `FileFacts` and parse it on first access.
   Alternatively, parse it only where metadata is used (similar, inventory).
3. `exact.py`: one read per file, not one per step.
4. `prepare`: when `PRAGMA user_version` already equals `SCHEMA_VERSION`, skip the DDL and do
   not write.
5. `services/audit.py` + `services/listing.py`: one connection for the whole audit.
6. Measure with 0131 before and after. Keep the change only if it saves time on the real
   collection.

## Acceptance

- A warm audit issues one `SELECT` of the files table, not one per file. A test counts the
  statements with `connection.set_trace_callback`.
- An index of an older schema still upgrades (`tests/fixtures/`).

## Status — PARTIAL (2026-10-14)

### Done
- `FactsRepository.preload(roots)` (`index/preload.py`): one `SELECT` per mounted folder,
  rows parsed once into path → (size, mtime, facts); `get` answers from it (a path below a
  preloaded folder and absent is unknown, no `SELECT`), `put`/`forget`/`move` keep it in step.
  The audit preloads right after `forget_missing` (timed as the `cache` stage of 0131).
- `exact.py` needs no change: its repeated `get` calls are now dictionary reads.
- `schema.prepare` returns at once when `PRAGMA user_version` is already `SCHEMA_VERSION`: no
  DDL, no write.
- `services/listing.list_media` opens the index once (load, walk, save) instead of twice; the
  audit's analysis and near-duplicate checks share one connection and one pool (0132). An audit
  now opens the index 2 times instead of 3.
- Tests: `tests/integration/test_index_one_pass.py` traces the statements (no per-file `SELECT`,
  no `CREATE TABLE` on a warm audit) and checks that an index of version 9 still upgrades.

### Not done
- Lazy metadata parsing (item 2). **Reason:** the audit needs the metadata of every file
  anyway (`take_inventory`, `IntegrityFindings.metadata`), so parsing on first access would
  save nothing there; each row is now parsed once instead of once per `get`.
- A single connection from the listing to the end (item 5, fully). **Reason:** with `prepare`
  skipped, a second open costs a file open; passing the repository into `list_media` (shared
  with `classify`) was not worth the change.
- Measure before/after on the real collection (item 6). **Reason:** needs the maintainer
  (0104 §7: the `cache`, `checks` and `fingerprints` figures of the step line).
