# 0035 — `classify` rules: calendar, date ranges, paths, cameras, kinds; the example taxonomy

- **Priority**: High
- **Batch**: classify
- **Depends**: 0026, 0027
- **Files**: `src/media_hygiene/classify/rules/` (new: `calendar.py`, `matchers.py`, `order.py`), `src/media_hygiene/classify/models.py`, `src/media_hygiene/classify/bands.py`, `src/media_hygiene/config/settings.py`, `src/media_hygiene/config/templates/config.toml.j2`, `src/media_hygiene/cli/cmd_classify.py`, `documentation/en/sort/`, `documentation/fr/sort/`

## Context

Split from 0026 on 2026-09-29 to keep each TODO a reviewable unit: the engine of 0026 works and
is tested without any rule. Rule names show as reasons in the workbook of 0027.

Rules are how the user writes down, once, what they know: "we were in Italy from 1 to 15 July
2023", "Léa's birthday is on 12 March", "the drone's pictures go to Drone". `classify` applies
them at every run, to next year's photos too. A workbook edit (0027) fixes one proposal; a rule
fixes every future one, and survives every re-run.

## Proposal

**Calendar**, applied to the events (0026) that overlap a date:
- **Recurring dates** → category. The defaults are examples in the interface language of the
  generated `config.toml`: Christmas 24–26/12, New Year 31/12–1/1; Saint-Nicolas 5–6/12 in the
  French template. The user adds birthdays and any other date.
- **One-off date ranges** → category: `2023-07-01..2023-07-15` → `Vacances/Italie 2023`. A trip
  without GPS (the common case, 0026) in one line.

**Ordered rules** in `[[classify.rules]]`. Each rule has a `name`, shown as the reason in the
summary and in the workbook. The first match above `sure` wins. Rule kinds:
- `existing_folder`, `event_neighbour`: the built-in signals of 0026, now orderable;
- `calendar`, `date_range`;
- `kind`, from metadata only (the vision model is unreliable here, 0029):
  - documents and screenshots: PNG without camera, screenshot name patterns, tiny images;
  - images received through a messaging app (`IMG-…-WA…`, `received_…`): no EXIF, dated by
    their name;
  - downloaded films and series, recognised by their name (`S01E05`, `1080p`, a release
    group): not memories, never laid out by default (as sorta's `not_personal` flag);
- `path`: a regular expression on the host path or the file name → category
  (`(?i)kermesse` → `École/Kermesse`);
- `camera`: a regular expression on make / model → category (a drone, an action camera, a
  child's camera);
- `place` / `trip` (0030) and `subject` (0029) plug in later;
- the fallback `other_category`.

**Confidence**: each rule kind has a default score in the table of 0026; a rule may set its own
`score` (a date range the user wrote is sure).

**Default taxonomy**: an **example**, written in the generated `config.toml` in the interface
language, which each user replaces.
- Occasion- and activity-based: Parties (Christmas, Saint-Nicolas, New Year, birthdays),
  Holidays and outings, School, Sport and leisure, Home and works, Animals, Nature and
  landscapes, Documents and screenshots, Other.
- A comment warns against a "Family / portraits" category: in a family collection it swallows
  most photos (7 of 12 in the 0029 sample).
- "Other" means "sure nothing matches"; "manual" means "we do not know".

**Feedback to the user**:
- The summary counts, per rule, the files it decided: the user sees the effect of each line they
  wrote.
- A rule that decided nothing is listed (a typo in a regular expression, a wrong year).
- Load-time errors name the rule: invalid regular expression, unknown placeholder, a date that
  does not exist. Overlapping date ranges are a warning.

## Acceptance

- [ ] Unit tests: recurring date (across New Year), date range, path, camera, each `kind`,
      rule order, per-rule score, unused rule listed, invalid rule refused with its name.
- [ ] Default calendar and `[[classify.rules]]` in the config template (fr + en values),
      documented as an example; arrays of tables documented as not overridable by environment
      variables.
- [ ] Sort guide page en + fr ("write down what you know"); `reference-commands.md`; `.po`
      translated.
