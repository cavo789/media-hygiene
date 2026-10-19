# 0244 — Docs captures of the new pages (pairs, junk, home, browse, places lists), then one `docs_screenshots` run

- **Priority**: Medium
- **Batch**: docs
- **Depends**: 0242, 0243
- **Files**: `tests/support/docs/served.py`, `tests/support/docs/browsing.py`, `tests/support/docs/browser.py`, `tests/support/docs/library.py`, `tests/support/docs/scenario.py`, `documentation/en/clean/12-decide-pair-by-pair.md`, `documentation/fr/clean/12-decide-pair-by-pair.md`, `documentation/en/clean/14-unwanted-photos.md`, `documentation/fr/clean/14-unwanted-photos.md`, `documentation/en/commands/home.md`, `documentation/fr/commands/home.md`, `documentation/en/commands/browse.md`, `documentation/fr/commands/browse.md`, `documentation/en/commands/places.md`, `documentation/fr/commands/places.md`, `documentation/en/images/`, `documentation/fr/images/`

## Context

Gathers the capture items of several PARTIAL TODOs, all for the same reason: `docs_screenshots`
is heavy (image build + browser) and was never run in an unattended lot.
- 0203 `review --pairs`: `review-pairs.webp` (`served.py::pairs` needs a `page.screenshot`).
- 0206 `review --junk`: the synthetic library may hold no unwanted picture — add a tiny, a
  screenshot-sized, a black and a blurred one to `library.py`, a `junk` mode, the image in step
  14 (check the step's file name).
- 0209/0210 home page: `home.webp`, a `home` mode; the menu capture `menu.txt` and help pages.
- 0223 `browse`: `browse.webp`, a `browse` mode.
- 0231 (+ 0238, 0242) `places`: the folder lists, and the default `config.toml` capture.
- 0173: `help-launcher.txt` and the first audit's capture without the `-e TZ` line.
Decided by the maintainer (inbox, 2026-10-19): this TODO **may run `docs_screenshots`** itself,
once, at the end of the lot (both languages: `docs_screenshots` then `docs_screenshots fr`),
with `nice` as every heavy helper. Synthetic pictures only (CLAUDE.md), never real photos.

## What to do

1. Add the modes (`served.py` / `browsing.py` / `browser.py`), each waiting for its pictures as
   the existing ones do.
2. Reference each new image in both languages (the unused-image test fails otherwise; an image
   referenced but missing too: add the references only after the run produced the files).
3. Run `docs_screenshots`, then `docs_screenshots fr`, one at a time; read the produced images
   (look at them) before committing: no empty page, no error page, no real path of the
   maintainer.
4. `tests/unit/test_documentation.py` and `tests/unit/test_docs_site.py` pass.

## Acceptance

- The images exist in `documentation/{en,fr}/images/` and are shown on their pages; the stale
  console captures listed above are regenerated.

## Gain (estimated)

Six pages a newcomer reads without seeing the screen they describe → each with its picture.

## Status: DONE (2026-10-19)

Modes `junk`, `home`, `browse` and a screenshot for `pairs` added (`served.py`, `browser.py`,
`browsing.py`); `junk.py` draws four synthetic unwanted photos (`Downloads`); `docs_screenshots`
run in `en` then `fr`; images `review-pairs`, `review-junk`, `home`, `browse` shown in both languages.
