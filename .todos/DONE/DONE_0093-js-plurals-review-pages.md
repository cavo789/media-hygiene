# 0093 — Review pages: real plurals for the counts known only in the browser

- **Priority**: Low — French reads "photo(s)", "série(s)" (review of the night fixes, 2026-10-11)
- **Batch**: i18n
- **Depends**: —
- **Files**: `src/media_hygiene/review/templates/review.html.j2`, `src/media_hygiene/review/templates/near_review.html.j2`, `src/media_hygiene/review/templates/near_review.js.j2`, `src/media_hygiene/review/templates/sort_review.html.j2`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/unit/test_french_counts.py`

## Context

The night fixes (2026-10-10) gave every count of the reports and the terminal its own
`ngettext`. The texts of the browser pages whose number is computed in the page itself still
use a "(s)" form, e.g. `review.html.j2`:
"Validate the {count} obvious series ({aside} shot(s) set aside)",
"{count} series still to see in {folder}: validate them as shown, {aside} shot(s) proposed aside".
The page cannot call `ngettext`: the number is known only after the template is rendered.

## Goal

- The template gives each counted fragment in both forms (`ngettext(..., 1)` and
  `ngettext(..., 2)`), e.g. `"aside": ["{n} shot set aside", "{n} shots set aside"]`, and a tiny
  JS helper picks one. French and English both use "one" for 0 and 1 in the forms they need
  (check French: 0 is singular, English: 0 is plural — use `Intl.PluralRules(locale)`).
- Same fragment pattern as the night fix (`sure_count`): a counted fragment inserted in the
  sentence, never a whole sentence per combination.
- Look at every page: `review`, `review --near`, `review-sort`, `places`, `people`, `search`.
- No "(s)" left in a `_()` of the templates (a test greps them).

## Acceptance

- French page: "1 photo mise de côté", "3 photos mises de côté"; English: "1 shot", "0 shots".
- The test of the night (`test_french_counts.py`) covers one page.
