# 0395 — *Your rules*: sorted by kind of rule, then by period, the latest first

- **Priority**: Medium
- **Batch**: review-sort
- **Depends**: 0393
- **Files**: `src/media_hygiene/review/sort_rules_view.py`, `src/media_hygiene/review/templates/sort_review_rule.js.j2`, `src/media_hygiene/review/templates/sort_review.html.j2`, `tests/integration/test_sort_review_rules.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/sort/06-write-down-what-you-know.md`, `documentation/fr/sort/06-write-down-what-you-know.md`

## Why

Maintainer, 2026-10-25, on the *Your rules* dialog (63 rules, 55 `path`): it lists the rules
in the file's order; he wants them sorted "on two levels: first the kind (date_range, path,
…), then the period, the most recent first".

## What

- The dialog's table sorted: first by kind (`date_range`, `path`, `calendar`, `kind`,
  `camera`, `subject`, `person`, `place`, `trip`, … then the built-in ones last), then by
  period, latest first: a `date_range` by its first day, any other rule by the first day of
  the event holding most of its files (0393's `first`); a rule that decided nothing last in
  its kind.
- A group heading per kind ("Dates (12)", "Folder names (43)"…), in the user's words, not
  the raw `match` values.
- The **order of `config.toml` is unchanged** (it decides which rule wins): say so in one
  line above the table ("Shown by kind and date; config.toml keeps its own order, which
  decides").
- Clicking a column heading sorts by it (name, files), a second click reverses; the default
  is the two-level order above.

## Tests

The view's order against a list mixing kinds and periods (two `date_range` of different
years, three `path` rules, a dead one, a built-in one); the file's order untouched after
the dialog was opened.
