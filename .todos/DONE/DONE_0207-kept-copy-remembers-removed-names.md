# 0207 — The kept copy remembers the folders and names of the copies `clean` removed (tags, search)

- **Priority**: Medium
- **Batch**: former-names
- **Depends**: —
- **Files**: `src/media_hygiene/index/former_names.py` (new), `src/media_hygiene/index/schema.py`, `src/media_hygiene/index/schema_tables.py`, `src/media_hygiene/index/parked.py`, `src/media_hygiene/index/pruning.py`, `src/media_hygiene/services/clean.py`, `src/media_hygiene/services/undo.py`, `src/media_hygiene/tags/models.py`, `src/media_hygiene/tags/producers.py`, `src/media_hygiene/config/templates/config.toml.j2`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/unit/test_former_names.py` (new), `tests/integration/test_former_names_follow.py` (new), `documentation/en/reference-tags.md`, `documentation/fr/reference-tags.md`, `documentation/en/clean/08-clean.md`, `documentation/fr/clean/08-clean.md`

## Context

Chosen by the maintainer on 2026-10-17 (proposal F4). When `clean` removes a copy, what its path
told is lost: a folder someone named (`Mariage Julie 2015`), a file name someone chose. The keep
policy keeps the most meaningful side (0012, 0014), but when both folders are meaningful, one name
goes. Competitors carry what the removed copy knew over to the kept one: Immich merges albums,
favourite, best rating, descriptions and tags when exactly one asset is kept (its docs,
2026-10-17); Mylio merges the metadata of deleted duplicates by default; Apple Photos merges.

In this tool the folders carry most of the meaning (the maintainer's collection: folder names
give the events and places; `tags` already turns folder and file names into words, `FOLDER` and
`NAME`). The journal already records, for each copy removed, the kept file (`JournalEntry.keeper`).

## What to do

- At each `clean` (exact and near tiers alike), for every copy moved or deleted that has a keeper:
  record (kept path, removed copy's host path) in a new index table, when the journal says the
  action is done (where `_forget_removed` reads the journal in `services/clean.py`).
- `undo` of that run removes its rows: the copy is back under its own name. `services/undo.py` is at
  187/200 and `index/schema.py` at 183/200: the table's statements and the removal live in the new
  `index/former_names.py`; the services only call it.
- The rows are keyed by the kept file's path: the table joins `PATH_TABLES`, so its rows follow the
  kept file when `sort` or `undo` move it (`moves`), are parked with a kept file that is set aside
  (`parked`), and are forgotten when the kept file is proven gone (`pruning`). Following
  `.claude/rules/workflow.md`: one test per event — moved by the tool, renamed or moved by the user
  (followed by 0147), deleted — and run the `cache-invalidation-reviewer` agent on the diff.
- `tags`: a new source `TagSource.FORMER`, "the meaningful words of the folders and names its
  removed copies had", computed like `FOLDER` and `NAME` from the recorded paths. `search` gets its
  column by itself (one per source); `xmp` writes it only when the user adds `former` to
  `[tags] xmp_sources` (default unchanged).

## Explicit non-goals

- `classify` hints from those folders: 0208.
- The metadata inside the copies (identical bytes for exact copies; near copies' EXIF): not merged.
- No change to which copy is kept.

## Acceptance

- Unit and integration: a clean writes the rows; its undo removes them; a sort moving the kept file
  carries them; a folder of the kept file renamed by the user carries them (0147); the kept file
  deleted forgets them; `tags` gives the former words; `search` finds the kept photo by a removed
  folder's word.
- Docs both languages: the new source in the tags reference; cleaning step 8 ("what a removed
  copy's folder said stays searchable on the kept photo").

## Gain (estimated)

Every folder or file name a clean removes stays searchable on the kept photo: on a newcomer's
collection, one name kept per removed copy whose folder differs from the kept one's.
