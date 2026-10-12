# 0110 — Docs: synthetic faces, then captures of the people page and the person rule

- **Priority**: Low — the step and the pages read well without pictures; captures come after
- **Batch**: docs
- **Depends**: —
- **Files**: `tests/support/docs/`, `documentation/en/sort/10-sort-by-person.md`, `documentation/fr/sort/10-sort-by-person.md`, `documentation/en/commands/people.md`, `documentation/fr/commands/people.md`, `documentation/en/reference-people.md`, `documentation/fr/reference-people.md`

## Context

TODO 0088 wrote step 10 of the sort guide ("Sort by person") without any capture: the
documentation demo (`tests/support/docs/`) draws synthetic pictures only, never real photos, and
none of them holds a face the real detector (YuNet, in the published image) would find. The
tests use plain coloured images and a fake finder (`tests/support/faces.py`), which is not the
image the captures run.

## Goal

1. **Choose the source of the faces** (the maintainer decides): generated faces (not real
   people), under a licence that clearly allows redistribution in a public repository and on
   GitHub pages (e.g. a dataset of AI-generated faces released CC0 / public domain). Research
   first, record the licence and the source in `tests/support/docs/` (an `ATTRIBUTION`/README
   line) — never photos of real people, never "free to use" without a written licence.
2. A handful of faces (3 people × 4–6 pictures each, plus one unknown) composed into the demo
   library's photos, so that `people` finds groups the detector really sees.
3. Captures (en + fr, `docs_screenshots`): the console of `people --sample` and `people`, the
   people page with one named group, and a `classify` block where a `person` rule decided
   (`<!-- capture: … -->`, like the other steps).

## Acceptance

- The source and licence of the faces are written next to them.
- `docs_screenshots` (en + fr) produces the new captures; step 10, `commands/people.md` and
  `reference-people.md` show them.
