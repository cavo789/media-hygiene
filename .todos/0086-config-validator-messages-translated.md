# 0086 — The reasons config validators give are translated, not English in a French sentence

- **Priority**: Low — only users with a wrong rule, place, pattern or time zone, in French
- **Batch**: config
- **Depends**: 0081
- **Files**: `src/media_hygiene/config/classify_rules.py`, `src/media_hygiene/config/classify_places.py`, `src/media_hygiene/config/zone.py`, `src/media_hygiene/config/patterns.py`, `src/media_hygiene/config/places_settings.py`, `src/media_hygiene/config/categories.py`, `src/media_hygiene/classify/rules/calendar.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/fr/sort/06-write-down-what-you-know.md`

## Context

Since 0081, a refused `config.toml` is explained in the user's language: the place (`« dates »
dans [[classify.rules]] n° 1 de config.toml`) and pydantic's common reasons are translated. The
reasons raised by the project's own validators (`ValueError(message)`) are kept as they are, and
about twenty of them are plain English f-strings, so a French user reads:

```
❌ [[classify.rules]] n° 1 dans config.toml : rule 'Anniversaire': '02-30' is not a day that exists.
```

## What to do

- Run every validator message through `_()` (`grep -rn "raise ValueError" src/media_hygiene/config
  src/media_hygiene/classify/rules`), with `{placeholders}` rather than f-strings, then
  `i18n_update` and translate. The settings are loaded once before the locale is installed
  (`i18n/bootstrap.py`, error swallowed) and again after it: the message shown is the second one.
- Update the French console block of `sort/06-write-down-what-you-know.md`.

## Acceptance

- A unit test loads an impossible rule date in French: no English words in the message.
