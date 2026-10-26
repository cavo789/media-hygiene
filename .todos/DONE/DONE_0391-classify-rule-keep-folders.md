# 0391 — A rule may keep the user's folders below its category (`keep_folders = true`)

- **Priority**: High
- **Batch**: classify
- **Depends**: 0385, 0386
- **Files**: `src/media_hygiene/config/classify_rules.py`, `src/media_hygiene/classify/rules/order.py`, `src/media_hygiene/classify/rules/building.py`, `src/media_hygiene/classify/workbook/own_folders.py`, `src/media_hygiene/config/templates/config.toml.j2`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/sort/06-write-down-what-you-know.md`, `documentation/fr/sort/06-write-down-what-you-know.md`

## Why

Maintainer, 2026-10-25: a trip is best written down as a `date_range` rule
(`Montenegro`, `2019-07-12..2019-07-19`, `Vacances et sorties/Montenegro`), created from the
review-sort page (0392). But the user already sorted that trip into
`2019/Montenegro/Budva`, `…/Cetinje`. Rules are read in order, the first sure one wins:

- a date rule **above** *Existing folders* puts every photo of the trip flat in
  `2019/Vacances et sorties/Montenegro`: Budva and Cetinje are lost (what 0385 forbids for
  an event choice);
- **below** it, Budva and Cetinje stay in `2019/Montenegro/…` and only the loose photos and
  the daughters' go to `2019/Vacances et sorties/Montenegro`: one trip, two places.

## What (decided by the maintainer, 2026-10-25: the third way)

- A rule field `keep_folders = true` (any rule with a category; written by 0392 on every
  rule it creates): the rule's category becomes the **parent**, the files of the folders the
  user named (`existing-folder`) keep the part of their path under the deepest common parent
  of those folders, as 0385 does for an event given a destination
  (`own_folders.OwnFolders.under`, reused, not copied): `…/Vacances et sorties/Montenegro/Budva`,
  `…/Montenegro/Cetinje`. One named folder only: the category itself.
- Loose files and person folders of the same dates join their session's folder under the
  category (0386's `same_moment`), else the category.
- The rule then sits above *Existing folders* (0392 places it there).
- Without `keep_folders`, nothing changes.

## Tests

The Montenegro case as a synthetic plan: two named folders and a person's folder over three
days, one `date_range` rule with `keep_folders` → `…/Montenegro/Budva`, `…/Cetinje`, the
person's photos in their session's folder; the same rule without it → flat (today); one
named folder → the category itself.
