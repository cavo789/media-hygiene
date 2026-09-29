# 0034 — Split the documentation into a Clean guide and a Sort guide

- **Priority**: Medium — must land before the first sort page (0026 depends on it)
- **Batch**: docs
- **Depends**: —
- **Files**: `README.md`, `README_FR.md`, `documentation/en/`, `documentation/fr/`, `tests/unit/test_documentation.py`, `tests/support/docs/__main__.py`, `tests/support/docs/pages.py`, `CLAUDE.md`

## Context

`documentation/en|fr` is one step-by-step guide about duplicates: audit → cache → report →
configuration → clean → undo → bursts → near duplicates → pairs → second opinion. Sorting
(`classify` / `sort`, 0026–0036) is a second goal with its own walk: someone who only wants to
sort must not read eight pages about duplicates first, and the reverse.

Several pages serve both goals: the first audit (it fills the index that `classify` reads),
the cache, several folders and disks, the configuration file, `undo` / `history` (a sort run is
undone like a clean run, 0024), and every reference page.

## Proposal

- **Three parts** in each language, same file names in `en/` and `fr/`:
  - `start/`: the shared first steps (first audit, cache, several folders, configuration file);
  - `clean/`: the current duplicate pages, renumbered from 1 (report, kept copy, file types,
    clean, undo, bursts, near duplicates, pairs, second opinion);
  - `sort/`: empty for now; 0026 writes its first page there. No placeholder page: a page
    exists only once its feature does.
  - Reference pages and `development.md` stay at the root; `images/` stays shared.
- **The entry page** (`documentation/<lang>/README.md`) asks "what do you want to do?": clean
  the duplicates, or sort the photos. It recommends cleaning **before** sorting (otherwise both
  copies are sorted, one of them renamed ` (2)`), without forcing it.
- **The root READMEs** keep the quick start (an `audit`) and list the two guides.
- `undo` / `history` / `purge` moves to `start/` or stays in `clean/` with a link from the sort
  guide: decide while writing; the page must not describe `sort` before 0028 exists.
- Old page paths are linked from outside (issues, the Docker Hub description): check the Docker
  Hub text and fix it in the same change.
- Tooling: `docs_screenshots` globs `*.md` in one folder only (`__main__.py`) → `rglob`; image
  links become `../images/…` in sub-folders; `test_documentation.py` already uses `rglob`.
- `CLAUDE.md` describes the new layout (user guide first, per goal, developer page last).

## Acceptance

- [ ] Every page reachable from `documentation/<lang>/README.md`, en and fr identical in names.
- [ ] `test_documentation.py` green (links, anchors, parity, unused screenshots).
- [ ] `docs_screenshots` regenerates the same captures into the moved pages (`git diff` shows
      moves and link changes only).
