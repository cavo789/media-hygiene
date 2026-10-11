# 0095 — `classify`: a `match = "person"` rule, to file photos by who is on them

- **Priority**: Medium — the reason `people` exists (0058: *file* photos by who is in them)
- **Batch**: people
- **Depends**: 0091
- **Files**: `src/media_hygiene/classify/rules/kinds.py`, `src/media_hygiene/classify/rules/matchers.py`, `src/media_hygiene/classify/rules/building.py`, `src/media_hygiene/config/classify_rules.py`, `src/media_hygiene/services/classify_inputs.py`, `src/media_hygiene/people/naming.py`, `src/media_hygiene/search/people_words.py`, `src/media_hygiene/config/templates/config.toml.j2`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/sort/06-write-down-what-you-know.md`, `documentation/fr/sort/06-write-down-what-you-know.md`, `documentation/en/reference-people.md`, `documentation/fr/reference-people.md`, `tests/unit/`, `tests/integration/people/`

## Context

0091 gave the groups of faces a name (`[[people.person]]` in `config.toml`) and made the
names searchable: `search person:chloe` builds, at each start, the names of the people on
each photo from the faces of the index (`search/people_words.py`, `people/naming.py`:
confirmed faces, then the nearest confirmed face above `[people] similarity`). Nothing in
`classify` reads those names yet, so the photos cannot be *filed* by person, which is what
0058 decided `people` is for (finding someone's photos is Immich's job). The sort guide step
(0088) waits for this rule.

## Goal

- A rule `match = "person"` with `names = ["Chloé", "Manon"]` (any of them; `all = true`
  for every one), giving its `category` like the other rules; reasons name the rule.
- The names of each photo come from the same code as `search` (`people_words`, moved to a
  shared place if needed), read once per `classify` run from the index and `config.toml`;
  suggestions never count.
- Events: decide (and document) whether an event is "with Chloé" when one photo has her,
  or a share of them (`min_share`?), as `subject` rules do with samples.
- A name in a rule that nobody has in `[[people.person]]` is refused at load time, naming
  the rule (as 0094 does for other config errors).
- Docs en + fr: the rule in sort step 6 and in `reference-people.md` ("Not there yet" shrinks).

## Explicit NON-goals

- The sort guide step "Sort by person" (0088), the XMP `PersonInImage` field (0074), the
  inventory column: later TODOs.

## Acceptance

- `classify` with a `person` rule puts the events with a named person into its category, in
  tests with synthetic faces and fake vectors only.
- A rule naming an unknown person is refused with its name.
- Docs en + fr; `.po` translated.
