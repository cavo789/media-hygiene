# 0394 — A date rule: the event's main folder becomes its folder, unrelated folders are not nested, screenshots are never taken

- **Priority**: High
- **Batch**: classify
- **Depends**: 0391
- **Files**: `src/media_hygiene/classify/rules/kept.py`, `src/media_hygiene/classify/rules/building.py`, `src/media_hygiene/classify/rules/order.py`, `src/media_hygiene/classify/rules/matchers.py`, `src/media_hygiene/config/templates/config.toml.j2`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/unit/test_classify_moments.py`, `documentation/en/sort/06-write-down-what-you-know.md`, `documentation/fr/sort/06-write-down-what-you-know.md`

## Why

Found on the maintainer's real data, 2026-10-25, before his first sort: he turned the rule
*Mariage d'Hervé et Magda* into `date_range = "2017-08-05..2017-08-06"`,
`category = "Fêtes/Mariages/Mariage d'Hervé et Magda"`, `keep_folders = true` (0391).
Read in his plan of 2026-10-13 (`C:\Users\Christophe\media-hygiene\reports\
20261013-191349-classify\plan.json`, read-only), that evening is one event (`8ad2016bedb4`)
of 44 files: 14 in `2017\Août 2017\Mariage Hervé et Magda`, 25 of Manon (`Manon\…`), 4
screenshots (`Screenpresso\`, `Screenpresso\Thumbnails\`, 2017-08-06 10:32 and 16:57), 1 in
`2017\Développement Sep`. A date rule takes the whole event; `keep_folders` nests every
user-named folder below its category, since they share no parent:
`…\Mariage d'Hervé et Magda\Mariage Hervé et Magda` (the wedding inside itself),
`…\Mariage d'Hervé et Magda\Manon`, `…\Mariage d'Hervé et Magda\Screenpresso\Thumbnails`
(estimated from the plan: the rule was not run).

## What (decided by the maintainer, 2026-10-25)

- **The main folder is the rule's folder.** Among the user-named folders of an event a
  `keep_folders` rule takes, the one holding the most of its files is the category itself
  (`Mariage Hervé et Magda` → `Fêtes/Mariages/Mariage d'Hervé et Magda`, never below it).
- **Only its relatives stay below.** The user-named folders sharing a parent with the main
  one keep their part under that parent (`Montenegro/Budva`, `…/Cetinje` as in 0391); a
  folder sharing nothing with it (`Développement Sep`, a person's folder not listed in
  `person_folders`) goes to the category itself, flat, never as a sub-folder.
- **A date rule never takes a file a `kind` rule matches** (screenshots, received pictures,
  downloads), wherever that `kind` rule is listed: such a file is not a memory of the event;
  it keeps its own rule (*Documents and screenshots*). The maintainer's answer: "never take
  them". Applies to `date_range` and `calendar` rules.
- The maintainer added `person_folders = ["Manon", "Chloé"]` (0386) to his `config.toml`:
  Manon's photos then join the wedding's folder by their moment (`same_moment`), not a
  `Manon` sub-folder. Say it in step 6 next to `keep_folders`.

## Tests

The Hervé and Magda event as a synthetic plan (14 in the wedding folder, Manon's photos with
and without `person_folders`, two screenshots of the next morning, one photo in an unrelated
named folder): the wedding's files in the category itself, Manon's in it too (with
`person_folders`), the screenshots under *Documents and screenshots*, the unrelated photo in
the category flat; Montenegro (0391's test) unchanged.
