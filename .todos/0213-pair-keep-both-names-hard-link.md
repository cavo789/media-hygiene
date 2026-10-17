# 0213 — A folder pair can keep both names: each copy becomes a hard link to the kept file (same drive)

- **Priority**: Low
- **Batch**: actions
- **Depends**: 0203
- **Files**: `src/media_hygiene/plan/review.py`, `src/media_hygiene/plan/models.py`, `src/media_hygiene/report/decisions.py`, `src/media_hygiene/report/templates/report.html.j2`, `src/media_hygiene/report/templates/_decisions.html.j2`, `src/media_hygiene/review/pairs_app.py`, `src/media_hygiene/review/templates/pairs_review.html.j2`, `src/media_hygiene/actions/kinds.py`, `src/media_hygiene/actions/clean.py`, `src/media_hygiene/actions/clean_links.py` (new), `src/media_hygiene/actions/reversal.py`, `src/media_hygiene/actions/undo.py`, `src/media_hygiene/actions/album_links.py`, `src/media_hygiene/cli/clean_confirm.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/integration/test_clean_links.py` (new), `documentation/en/clean/12-decide-pair-by-pair.md`, `documentation/fr/clean/12-decide-pair-by-pair.md`, `documentation/en/reference-safety.md`, `documentation/fr/reference-safety.md`, `documentation/en/commands/clean.md`, `documentation/fr/commands/clean.md`, `documentation/en/commands/undo.md`, `documentation/fr/commands/undo.md`, `tests/measure/mh-measure.ps1`
- **Needs maintainer**: after the work, one run on Windows: a pair linked through Docker Desktop's file sharing — Explorer shows both files, both open, the free space grows; then a photo of the pair edited and saved in the Photos app: does the other name change too (write down what was seen)

## Context

Chosen by the maintainer on 2026-10-17 (proposal F10). For a pair of folders that both mean
something (`Best of 2019` and `2019\07`), one side loses its copies today. Duplicate Cleaner Pro,
AllDup and Google Takeout Helper (`--hardlink` on Windows) can replace a duplicate by a hard link
(vendor pages, 2026-10-17): the space is freed and both folders still show the photo.

The tool already makes hard links through Docker Desktop (albums, 0041; moves, 0138), knows that
a hard-linked copy is no copy (`actions/verify.py`: `samefile`), and `undo` rebuilds a file from
the kept one (`COPY_FROM_KEEPER`).

## Design (proposed 2026-10-17)

- A fourth choice for a folder pair, *Keep both names (link)*, offered only when both folders are
  on the same drive (same device): in the report's list, and in `review --pairs` (0203) with its
  own key (`K`).
- `clean --decisions`, for each copy of such a pair: the byte comparison with the kept file (as
  before a deletion), then the copy is replaced by a link to the kept file in one step: `os.link` to
  a temporary name in the copy's folder, then `os.replace` over the copy, so the name is never
  missing. Journaled as a new action kind (`link-duplicate`, with the kept file). Across drives:
  refused, said.
- `undo`: the name becomes an independent file again (a copy of the kept file to a temporary name,
  then `os.replace`), as `COPY_FROM_KEEPER` does.
- Said plainly — in the report, the docs and the question before cleaning: a link is one photo
  under two names; an edit saved in place shows under both names; deleting one name frees nothing
  while the other remains; a backup tool may count both.

## What to do

- Size caps: `actions/clean.py` (200/200), `report/decisions.py` (200/200), `plan/models.py`
  (197/200), `actions/undo.py` and `actions/reversal.py` (193/200), `cli/clean_confirm.py`
  (178/200): the link action and its reversal go to new modules (`actions/clean_links.py`), reusing
  what `actions/album_links.py` already checks; the link decision's model to a new `plan` module.
- `PairAction.LINK` in `plan/review.py`; `apply_choices` turns the pair's copies into link
  actions instead of removals.

## Explicit non-goals

- Near duplicates (their bytes differ): never linked.
- Symbolic links or Windows shortcuts.

## Acceptance

- Integration (Linux): the link is made after the byte comparison, the two names share one inode
  after, a pair across devices is refused, a run stopped in the middle leaves either the old file
  or the link under each name (never nothing), `undo` gives two independent files with the same
  bytes.
- Docs both languages (step 12, safety page, `clean` and `undo` pages).
- Windows (maintainer): the run above, its result written into the docs (what an edit in Photos
  does).

## Gain (estimated)

For pairs of meaningful folders: the copies' space freed without losing either folder's view of
the photos.
