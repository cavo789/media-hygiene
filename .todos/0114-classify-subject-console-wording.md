# 0114 — `classify`: the subject lines explain their numbers (groups, samples, cache, files)

- **Priority**: Medium — the maintainer could not read them on the first real run
- **Batch**: classify
- **Depends**: —
- **Files**: `src/media_hygiene/console/subject_view.py`, `src/media_hygiene/services/subject_plan.py`, `src/media_hygiene/services/subject_answers.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/integration/subjects/test_classify_subjects_edges.py`, `documentation/en/sort/08-subjects-from-a-local-model.md`, `documentation/fr/sort/08-subjects-from-a-local-model.md`

## Context

First real `mh classify --year 2015` (2026-10-12, review 0056) printed:

```text
42 événements ou photos isolées n'ont pas de signal plus fort que leur sujet : 79 photos répondent pour eux.
Dont 78 à décrire avec qwen3.8:27b-mtp-q4_K_M, environ 2 min 29 s.
✅ 78 photos décrites ; gardées dans le cache.
Règle 'Sujet' : un sujet pour 200 fichiers.
```

The maintainer asked what 42 / 79 / 78 / 200 meant. Every number is right; none explains
itself: "signal plus fort que leur sujet" is jargon, "répondent pour eux" does not say that the
model sees up to `samples_per_event` photos per event and the others follow, the one photo
already in the cache is implicit in 79 → 78, and nothing says what became of the groups that got
no subject.

## What to do

Reword in `subject_view.py` (both catalogues), keeping the same facts:

```text
42 groupes de photos (événements ou photos seules) ne sont pris par aucune de vos règles :
le modèle en regardera 79 (jusqu'à 3 par événement, les autres suivent).
78 à décrire avec qwen3.8:27b-mtp-q4_K_M (1 déjà dans le cache), environ 2 min 29 s.
✅ 78 photos décrites ; gardées dans le cache.
Règle 'Sujet' : 200 fichiers rangés d'après ce qu'a vu le modèle ; 12 groupes sans sujet → À trier.
```

- "jusqu'à N" comes from `[classify.ai] samples_per_event`, never a literal 3.
- "(N déjà dans le cache)" only when N > 0 (samples − missing).
- The last clause needs the number of units left without a subject (model said none, or the
  samples disagreed): take it from what `subject_answers` already decides; if it is not kept
  there, add it to `Answered` rather than recomputing in the view. Name the band the way the
  console names it elsewhere (`unsure`/`manual` layouts: "À vérifier" / "À trier").
- English wording to match ("groups of photos (events or lone photos) no rule of yours took: the
  model will look at 79 of them (up to 3 per event, the others follow)").
- Update the console block of `sort/08-subjects-from-a-local-model.md` (en + fr), then
  `i18n_update` and the French translations.

## Explicit NON-goals

- The `--sample` table and its time line (0029 measures; French descriptions are their own TODO).
- The *Why* table and the "rules that decided nothing" warning.

## Acceptance

- The four lines read as above in French and English; the cached count and the groups without a
  subject appear only when non-zero.
- `test_classify_subjects_edges.py` asserts the new wording; the docs blocks match.
