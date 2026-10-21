# 0268 — The pages of `review` wear the home page's look: one theme and one header for every page, first on the review boards

- **Priority**: Medium — asked by the maintainer (2026-10-20): "every web page the tool creates should reuse the new template"
- **Batch**: review-ui
- **Depends**: 0266
- **Files**: `src/media_hygiene/review/local_app.py`, `src/media_hygiene/review/templates/theme.css.j2` (new), `src/media_hygiene/review/templates/page_header.html.j2` (new), `src/media_hygiene/review/templates/review.html.j2`, `src/media_hygiene/review/templates/near_review.html.j2`, `src/media_hygiene/review/templates/pairs_review.html.j2`, `src/media_hygiene/review/templates/unwanted_review.html.j2`, `src/media_hygiene/review/templates/gone_review.html.j2`, `src/media_hygiene/review/templates/sort_review.html.j2`, `src/media_hygiene/review/templates/phone_review.html.j2`, `src/media_hygiene/review/templates/review_board.css.j2`, `src/media_hygiene/review/templates/review_compare.css.j2`, `src/media_hygiene/review/templates/review_side.css.j2`, `src/media_hygiene/review/templates/review_tree.css.j2`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/unit/test_page_headers.py` (new), `documentation/en/images/`, `documentation/fr/images/`

## Context

0266 gives the home page the avonture.be look and the meerkat. The other pages keep the
GitHub-like tokens of today's `home.html.j2`, so going from the home page to one of them
changes the visual world. The maintainer asked (2026-10-20) that every page the tool serves
reuse the new template, and that the documentation link at the top lead to the page's own
chapter: on `places`, the Places chapter.

Eleven pages (counted from the templates), split by family so each TODO opens one folder:

- the review boards: this TODO;
- `search` and `browse`: 0271;
- `places` and `people`: 0272;
- the HTML reports, files opened without a server: 0273.

**Each command keeps its own server.** A page's sidebar could not link to the home page's
spaces while the home server is stopped, so the shared part is a header, not the whole shell.
One server for every page would be another, much larger change.

## What to do

1. **One theme partial** (`theme.css.j2`):
   - the `--mk-*` and `--mh-*` tokens, light and dark, following the OS, then the switch of 0266
     (read from the same `localStorage` key);
   - the fonts and images of `/assets/`. 0266's route moves into `review/local_app.py`, the
     base most page servers share, so every page built on it serves them.

   Every page includes it in place of its own colours. The boards' layout and keys do not
   change.
2. **One header partial** (`page_header.html.j2`) for every page:
   - "Media Hygiene", the avatar, and the page's name;
   - "Documentation" in the page's language, plus its English or French twin, both opening the
     page's chapter (0265's catalog `doc`, or 0270's local page once it exists);
   - "Back to the home page", where the page was opened from it. It ends the page as Quit does,
     and the `mh` loop brings the home page back (0210).
3. **The seven review pages** use both: `review` and its `--near`, `--pairs`, `--junk` and
   `--gone` modes, `review-sort`, and the page of `mh phone --free`.

## Acceptance

- `tests/unit/test_page_headers.py`: each of the seven pages renders its header, and its two doc
  links lead to its chapter in both languages (the pages exist: `test_documentation.py`'s
  helpers).
- The keys of each board work as before (their existing tests pass unchanged).
- Every capture under `documentation/{en,fr}/images/` that shows a review page goes stale: say
  that `docs_screenshots` should run (heavy, by the maintainer).

## Gain (counted)

- Seven pages move to the look of the home page, and the help for each one is a click away, in
  both languages.
- The two partials serve 0271, 0272 and, adapted, 0273: the theme is written once.
