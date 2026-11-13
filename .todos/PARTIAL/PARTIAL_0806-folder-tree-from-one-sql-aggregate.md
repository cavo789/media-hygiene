# 0806 — Folder tree counted by SQLite, not by a Python walk of every row

- **Priority**: High
- **Batch**: page-speed
- **Depends**: 0804
- **Files**: `src/media_hygiene/search/folders.py`, `src/media_hygiene/search/folder_tree.py`, `src/media_hygiene/search/statements.py`, `src/media_hygiene/index/schema.py`, `src/media_hygiene/index/schema_tables.py`, `tests/unit/test_folder_tree.py`, `tests/measure/pages-budget.md`

Filed by the speed review of 2026-11-13. 0804 keeps the tree between two requests; this
TODO makes the first build itself cheap (the one paid at each start, or ahead).

## Context

`GET /api/folders` runs `SELECT path, size FROM files` and counts in Python
(`folder_counts`: a `Path` per row, the suffix's media kind, every ancestor folder
updated per file): *measured* (pages-budget, 2026-11-11) 2,956 ms at 100,000 files and
8,852 ms at 300,000, cold and warm alike. The maintainer's 52,000 files: *estimated*
1.5 s per opening of the folder view.

## Proposal

- Measure first on the synthetic index of `tests/measure/pages/library.py` at 100,000 and
  300,000: (a) the current walk; (b) one `GROUP BY` on the parent folder (an expression
  on `path`, or a generated `folder` column with an index, schema bump) that returns
  one row per **direct** folder with its photos, videos, files and bytes, the ancestors
  summed in Python over the folders only (thousands, not hundreds of thousands); (c) the
  same with `media_kind` decided in SQL by suffix (`CASE`) vs in Python per folder row.
- Keep the result identical: a test comparing the new tree with `folder_counts` kept as
  the reference on random trees (empty, one file, a file at a root, nested dumps, suffixes
  in upper case, a sidecar, a video).
- A generated column, if chosen, is written by `schema.upgrade` in place and read by the
  folder queries of `search/statements.py` (`FOLDER_FILES`) too.

## Acceptance

- [ ] The three variants measured at 100,000 and 300,000 in the TODO's status; the one kept
      under 300 ms at 300,000 (*target*, estimated from thousands of folder rows)
- [ ] Equivalence test against `folder_counts` on random trees
- [ ] `tests/measure/pages-budget.md` rerun: the `folders` rows updated, budget lowered

## Where the user gains

Estimated: the folder view's first opening on 52,000 files from ≈ 1.5 s to under 0.1 s;
with 0804, every later opening is a lookup.

## Status — PARTIAL (2026-11-13)

### Done
- Measured (scratch script on the bench's synthetic index, best of 3, `nice -n 19`):
  (a) the current text-only walk (`folder_counts`, 0704): 99 ms at 100,000, 305 ms at
  300,000; (b) one `GROUP BY` on the parent folder and suffix as SQL expressions:
  303 ms and 922 ms (3× slower: the sort of computed strings); (c) moot (b loses
  before the kind is decided).
- Kept (a): no product change. With 0804 the tree is kept: warm 2.8 ms (100,000), 7.5 ms
  (300,000); `pages-budget.md` rows and budgets updated.

### Not done
- A generated `folder` column with an index (schema bump). **Reason:** not measured; the
  cold build is 126 ms at 100,000 and paid once (ahead, by the warm-up); a schema bump
  for ≈ 200 ms at 300,000 needs the maintainer's call.
- The equivalence test: nothing replaced `folder_counts`.
