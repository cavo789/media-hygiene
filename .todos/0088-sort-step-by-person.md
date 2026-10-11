# 0088 — Sort guide: a step "Sort by person", once the `person` rule exists

- **Priority**: Low — documentation follow-up, nothing to write before the rule ships
- **Batch**: people
- **Depends**: 0058
- **Files**: `documentation/en/sort/`, `documentation/fr/sort/`, `documentation/en/sort/quick-guide.md`, `documentation/fr/sort/quick-guide.md`, `documentation/en/reference-people.md`, `documentation/fr/reference-people.md`, `documentation/en/README.md`, `documentation/fr/README.md`, `tests/support/docs/`

## Context

`people` (0058, first slice) finds and groups faces, read-only. For now, the documentation has a
command page (`commands/people.md`) and a reference page (`reference-people.md`). It has no
step in the step-by-step guides, because nothing can be sorted by person yet. The maintainer
confirmed this (review of 2026-10-11): reference page now, a "Sort" step later.

## Goal

When naming (`[[people]]`) and the classify rule `match = "person"` exist (rest of 0058), add a
numbered step to `documentation/{en,fr}/sort/`, after `09-places-from-gps.md` (number it then):

- run `people`, judge the groups on the page, name them;
- write the `person` rule in `config.toml`, then `classify` / `review-sort` / `sort` as in the
  previous steps;
- privacy line (faces stay in `/cache`, `people --forget`), cost (`people --sample`);
- link it from `quick-guide.md`, the documentation `README.md` and `reference-people.md`.

Screenshots come from `docs_screenshots` with synthetic faces only (`tests/support/docs/`),
never real photos.

## Acceptance

- The step exists in both languages, same file name, linked from the sort quick guide.
- `tests/unit/test_documentation.py` passes (links, anchors, parity, screenshots).
