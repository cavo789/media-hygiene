# 0345 — Search: a person and words in one sentence ("Papy dans le jardin")

- **Priority**: Medium
- **Batch**: search
- **Depends**: 0344
- **Files**: `src/media_hygiene/search/query.py`, `src/media_hygiene/search/statements.py`, `src/media_hygiene/search/people_words.py`, `src/media_hygiene/tags/normalize.py`, `src/media_hygiene/search/templates/search.html.j2`, `tests/unit/test_search_query.py`

## Context

Asked by the maintainer (2026-10-24): search `Papy dans le jardin` — a person (`Papy` works with
*Words of: person*) mixed with words.

## Today (read in the code, not run on their index)

- Every word is ANDed across all sources (`query.py`, `statements.conditions`): `Papy jardin`
  already means *Papy* (person source) **and** *jardin* (any source).
- But the query keeps its little words: `dans` and `le` must be in the index too, and the index
  drops them as stop words when it is built (`tags/normalize.py`). A natural sentence therefore
  finds nothing. `jardin` itself also needs the vision words (0344).

## To do

1. The query drops the stop words of `[tags]` (and words of one or two letters) the way the
   index does; a phrase in quotes is kept as typed.
2. A word that is a person's name is matched in the person source (no need for `person:`); the
   line under the search shows how it was read: `Papy (person) + jardin`.
3. Tests: `Papy dans le jardin` = `person:papy jardin`; `"dans le jardin"` kept as a phrase.

## Acceptance

- [ ] `Papy dans le jardin` finds the photos of Papy with *jardin* in any source.
- [ ] Docs en + fr (*How to write a search* and `commands/search.md`).
