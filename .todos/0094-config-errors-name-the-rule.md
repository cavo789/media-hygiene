# 0094 — Config errors: name a rule or a place by its `name`, not only its number

- **Priority**: Low — comfort (review of 0081, 2026-10-11)
- **Batch**: config
- **Depends**: —
- **Files**: `src/media_hygiene/config/explain.py`, `src/media_hygiene/config/origin.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/unit/test_config_errors.py`, `documentation/en/sort/06-write-down-what-you-know.md`, `documentation/fr/sort/06-write-down-what-you-know.md`

## Context

Since 0081, a refused item of an array of tables is named by its position, counted from 1:
`[[classify.rules]] number 2 in config.toml` (`config/explain._table`). With a dozen rules, the
user has to count. Most rules and places carry a `name` (`name = "Birthday"`).

## Goal

- When the raw item has a `name` (read from the file layer, `Problems.layers`, before pydantic
  refused it), add it: `[[classify.rules]] number 2 ('Birthday') in config.toml`
  (French: `[[classify.rules]] n° 2 (« Anniversaire »)`). Keep the number: two rules may share a
  name, or the name itself may be the refused value.
- Same for `[[classify.places]]` and any other array of tables of the settings.
- No name, or a name that is not a string: the number alone, as today.

## Acceptance

- Unit tests: named rule, unnamed rule, refused `name`, a place.
- The error example of `sort/06-write-down-what-you-know.md` (en + fr) shows the name.
