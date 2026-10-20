# 0213 — A folder pair can keep both names: each copy becomes a hard link to the kept file (same drive)

- **Priority**: Low
- **Batch**: actions
- **Depends**: 0203
- **Files**: `src/media_hygiene/plan/review.py`, `src/media_hygiene/plan/models.py`, `src/media_hygiene/report/decisions.py`, `src/media_hygiene/report/templates/report.html.j2`, `src/media_hygiene/report/templates/_decisions.html.j2`, `src/media_hygiene/review/pairs_app.py`, `src/media_hygiene/review/templates/pairs_review.html.j2`, `src/media_hygiene/actions/kinds.py`, `src/media_hygiene/actions/clean.py`, `src/media_hygiene/actions/clean_links.py` (new), `src/media_hygiene/actions/reversal.py`, `src/media_hygiene/actions/undo.py`, `src/media_hygiene/actions/album_links.py`, `src/media_hygiene/cli/clean_confirm.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/integration/test_clean_links.py` (new), `documentation/en/clean/12-decide-pair-by-pair.md`, `documentation/fr/clean/12-decide-pair-by-pair.md`, `documentation/en/reference-safety.md`, `documentation/fr/reference-safety.md`, `documentation/en/commands/clean.md`, `documentation/fr/commands/clean.md`, `documentation/en/commands/undo.md`, `documentation/fr/commands/undo.md`, `tests/measure/mh-measure.ps1`

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
- Windows (maintainer, after the work; closes the TODO, implementing needs no maintainer — inbox 2026-10-19): one run on Windows: a pair linked through Docker Desktop's file sharing — Explorer shows both files, both open, the free space grows; then a photo of the pair edited and saved in the Photos app: does the other name change too (write down what was seen); its result written into the docs (what an edit in Photos
  does).

## Gain (estimated)

For pairs of meaningful folders: the copies' space freed without losing either folder's view of
the photos.

## Status — PARTIAL (2026-10-19)

### Done
- `PairAction.LINK` (`plan/review.py`): the pair's copies go to `KeepDecision.linked`, never
  removed; a swap in the same group spares them; a linked copy is not moved by a burst or
  `search` choice. `plan/pair_links.py`: `link_refusal` (two drive letters, two devices by the
  scan's identity, unknown identity, protected kept folder), counts and size.
- Offered in the report (*Keep both names (link)*, only when `linkable`) and in `review --pairs`
  (key `K`, refused when not linkable); `clean --decisions` refuses a link decision across
  drives or to a protected folder (`services/pair_checks.py`, the swap check moved there too).
- `actions/clean_links.py`: byte comparison (`checked_removal`), device check, journal
  `link-duplicate` (`pending`, `done`, `keeper`, `sha256`), `os.link` to a hidden draft
  `.<name>.media-hygiene-link` then `Path.replace` over the copy; EXDEV / no-link filesystems
  said in plain words; a draft left by a killed run is taken over, a user's file of that name
  stops the link.
- `undo` (`actions/link_undo.py`, `Reversal.SEPARATE_LINK`): copy of the name to a draft,
  proven identical, the copy's date back, `replace`; a name no longer a link is left and
  said; a `pending` entry whose name is no link was never done (`actions/undo_pending.py`).
- The question before cleaning says the phrase and what a link is (`console/link_view.py`);
  `history` counts the links in *Linked* and their bytes in *Freed* (not *Deleted*);
  `plan.csv` lists them; docs both languages (step 12, safety, `clean`, `undo`); French .po.
- Tests: `tests/integration/test_clean_links.py` (demo tree both ways, D: never offered,
  byte mismatch, EXDEV, stopped before the rename, killed after it, draft leftovers, undo
  cases, history), `tests/unit/test_pair_links.py`, `review --pairs` K, refused decision.
- Step 22 of `tests/measure/mh-measure.ps1`.

### Not done
- The Windows check (maintainer): image built from branch `iterate/2026-10-19`, then
  ```powershell
  cd C:\temp
  Invoke-WebRequest https://raw.githubusercontent.com/cavo789/media-hygiene/iterate/2026-10-19/tests/measure/mh-measure.ps1 -OutFile .\mh-measure.ps1
  Unblock-File .\mh-measure.ps1
  powershell -File .\mh-measure.ps1 -Only 22 -Count 3
  ```
  It links a pair through Docker Desktop, logs `fsutil hardlink list` and C:'s free space,
  asks what Explorer shows, then for a photo edited and saved in the Photos app (does the
  other name change too?), and undoes. Its result goes into the docs (step 12: what an edit
  in Photos does).
  **Reason:** only Windows + Docker Desktop can show whether `os.link` + `os.replace` through
  the file sharing make a true NTFS hard link, and what Photos does on save.

## Measured on Windows (2026-10-20, step 22 of mh-measure.ps1, maintainer, run `measures-20261020-1044`)

- `clean` keeping both names through Docker Desktop: 3 files processed, 0 failed; each photo has
  **2 names** in `fsutil hardlink list`, same bytes: a true NTFS hard link. C: gained 2,265,088
  bytes for 2,386,607 bytes of copies (95 %, measured; the rest is cluster rounding or other
  activity). Explorer shows and opens both folders.
- An edit: the Photos app is not installed on the maintainer's PC (`Get-AppxPackage
  Microsoft.Windows.Photos` empty), so **Paint.NET** was used (the log line says "in Photos":
  it was Paint.NET). Its save **wrote a new file**: the edited name changed, its twin did not,
  1 name left — the link separated, nothing lost. Paint.NET also re-encoded the JPEG at 75 %
  quality (its own save dialog, not mh).
- `undo`: 2 processed, 1 skipped "it is an independent file already" (the edited one, left
  alone as designed); afterwards each name has 1 name, the untouched two back to their 2002 dates.
- Docs en + fr step 12: the editor-saving-a-new-file case added (Paint.NET, measured). The
  Photos app itself stays unmeasured (not on this PC); not worth a TODO.
- Every item done → closed DONE.
