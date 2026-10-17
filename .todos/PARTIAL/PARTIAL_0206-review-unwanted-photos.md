# 0206 — `review --junk`: the photos most likely unwanted (tiny, screenshots, black, blurriest), set aside only by you

- **Priority**: Medium
- **Batch**: review
- **Depends**: 0203
- **Files**: `src/media_hygiene/cli/review_modes.py`, `src/media_hygiene/cli/review_options.py`, `src/media_hygiene/plan/unwanted.py` (new), `src/media_hygiene/config/review_settings.py`, `src/media_hygiene/config/templates/config.toml.j2`, `src/media_hygiene/classify/rules/matchers.py`, `src/media_hygiene/services/unwanted_reviewing.py` (new), `src/media_hygiene/review/unwanted_app.py` (new), `src/media_hygiene/review/unwanted_views.py` (new), `src/media_hygiene/review/unwanted_file.py` (new), `src/media_hygiene/review/templates/unwanted_review.html.j2` (new), `src/media_hygiene/review/templates/unwanted_review.js.j2` (new), `src/media_hygiene/report/decisions.py`, `src/media_hygiene/services/review.py`, `src/media_hygiene/plan/review.py`, `src/media_hygiene/actions/kinds.py`, `src/media_hygiene/actions/reversal.py`, `src/media_hygiene/actions/clean.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/unit/test_unwanted.py` (new), `tests/integration/test_unwanted_review.py` (new), `tests/support/docs/pages.py`, `documentation/en/clean/14-unwanted-photos.md` (new), `documentation/fr/clean/14-unwanted-photos.md` (new), `documentation/en/README.md`, `documentation/fr/README.md`, `README.md`, `README_FR.md`, `.config/mkdocs/mkdocs.yml`, `documentation/en/commands/review.md`, `documentation/fr/commands/review.md`

## Context

Chosen by the maintainer on 2026-10-17 (proposal F3). Competitors clean more than duplicates:
Google Photos and Files by Google propose blurry photos, screenshots and large videos (per
third-party articles); Microsoft Photos sorts screenshots, receipts, identity documents and notes
(Copilot+ PCs only, September 2025); PhotoPrism gives a quality score and keeps low ones for review;
digiKam 9 has an AI aesthetic detection; Excire Foto an aesthetic score.

Every fact needed is already in the index, measured by the audit: the size (width × height), the
sharpness (variance of the Laplacian), the exposure (mean brightness, shares clipped to black and
to white), and `classify`'s kind `screenshot` (`classify/rules/matchers.py`, `is_screenshot`:
screenshots, documents, tiny images). Measured on the maintainer's index (2026-10-17, 50,563
images): 2,512 under 0.16 MP; 414 files named like screenshots; 71 very dark (mean under 25, 70 %
black); sharpness percentiles 1 / 5 / 10 / 50 % = 15 / 52 / 95 / 530.

## Design (proposed 2026-10-17)

- Never automatic: a page to look at, like the bursts. Nothing is set aside until the user says
  so; `clean --decisions` then moves what was set aside to the quarantine (journaled, undoable).
- The reasons, each a setting of a new `[review.unwanted]` table (0 disables one):
  - tiny: under `tiny_megapixels` (0.16);
  - screenshot or document: `classify`'s kind (`is_screenshot`, the same function);
  - black or white: mean brightness under `dark_mean` (25) with at least `dark_share` (0.7) of the
    pixels black; the same for white (over 230, 0.7);
  - blurriest: sharpness under the `blur_percentile` (2) % of the collection's own images, so the
    threshold follows each collection and camera instead of a fixed number.
- Never listed: a file in a protected folder, a burst shot (`review` handles those), a member of a
  near-duplicate group, a backup file (0204, when it exists).
- The page: one group per reason, the largest first; every photo of a group proposed aside; the
  keys of the other reviews (`→` the group as proposed, `Space` keep or set aside the photo under
  the cursor, `←`, `N`, `U`); the reason under each picture. Choices saved at once under an
  `unwanted` key of `decisions.json`, read back and shown, the other keys kept.
- `clean --decisions` sets aside the photos marked, under a new action kind (`quarantine-unwanted`,
  undone like the other set-asides); the summary and `history` count them apart. The kind is one
  that 0216 remembers (a photo set aside that comes back is recognised): whichever of 0206 and 0216
  lands second adds it to that list.

## What to do

- Size caps: `actions/clean.py` (200/200), `report/decisions.py` (200/200) and
  `actions/reversal.py` (193/200) are full or nearly: the new action, the `unwanted` model and
  anything else go to new modules (0202 may have split `clean.py` already).
- The docs get a step 14 of the cleaning guide (no renumbering): the reasons, the settings, the
  page, `clean --decisions`; the guide lists (both READMEs, both `documentation/*/README.md`) and
  the mkdocs nav add it.
- A capture of the page (synthetic pictures only: a tiny one, a screenshot, a black one, a blurred
  one).

## Explicit non-goals

- Videos (very short pocket recordings): a later TODO if wanted.
- An AI model (aesthetics, closed eyes): only the facts already measured.
- Deleting: the quarantine, as everywhere; `purge` stays the only way to erase.

## Acceptance

- Unit: each reason and its threshold (0 disables), the percentile computed on the collection, the
  exclusions (protected, bursts, near groups).
- Integration: the page's state, a choice saved and read back, `clean --decisions` moves only what
  was marked, `undo` puts it back.
- Docs both languages; say in the report that `docs_screenshots` should run.

## Gain

Candidates measured on the maintainer's index (2026-10-17): about 2,500 tiny images, 400
screenshot names, 70 black photos, and 1,000 blurriest (2 % of 50,563, estimated from the
percentile). What the user sets aside is theirs to decide: no figure before a real review.

## Status — PARTIAL (2026-10-17)

### Done
- `plan/unwanted.py`: reasons screenshot (`classify`'s `is_screenshot`), tiny, nearly black, nearly
  white, blurriest (percentile of the collection's own sharpness, numpy's interpolation without
  numpy); one reason per photo; the reason with the most photos first.
- `[review.unwanted]` settings (`UnwantedSettings` in `config/review_settings.py`, documented in
  `config.toml.j2`): `tiny_megapixels`, `screenshots`, `dark_mean`/`dark_share`,
  `white_mean`/`white_share`, `blur_percentile`; 0 (or false) disables a reason.
- Never listed: protected folders, burst shots, near-duplicate and re-encoded video groups, exact
  duplicates' other copies (`SimilarFindings.images` holds only the compared pictures).
- `review --junk`: `services/unwanted_reviewing.py`, `review/unwanted_app.py`,
  `unwanted_session.py`, `unwanted_views.py`, `unwanted_file.py`, templates; pages of 40 photos
  per reason; `→` the group as marked, `Space`/click toggles, `↑`/`↓` cursor, `←`, `N`, `U`;
  choices saved under `unwanted` (every decided photo, `aside` true/false), read back and shown,
  the other keys kept.
- `clean --decisions`: new kind `quarantine-unwanted` (undone like the other set-asides), checked
  against the size and date seen (`chosen_blocker`), protected refused; the plan, the confirm
  line, the "Your decisions" line and `history` (*Of which unwanted* column) count them apart.
- Docs: step 14 of the cleaning guide (both languages), guide lists (both READMEs, both
  `documentation/*/README.md`), mkdocs nav, `review` command page; steps renumbered "of 14".
- Tests: `tests/unit/test_unwanted.py`, `tests/integration/test_unwanted_review.py`.

### Not done
- The screenshot of the page (synthetic: a tiny, a screenshot, a black, a blurred picture).
  **Reason:** images come only from `docs_screenshots` (not run in an unattended lot), and the docs'
  synthetic library may hold no unwanted photo (the command then serves no page): add such
  pictures to `tests/support/docs/library.py`, a `junk` mode in `served.py`/`browser.py`/
  `browsing.py`, run `docs_screenshots`, then show the image in step 14.
- 0216 (photos set aside that come back): when it lands, add `quarantine-unwanted` to the kinds it
  remembers.
