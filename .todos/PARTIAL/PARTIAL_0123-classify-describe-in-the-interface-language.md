# 0123 — `classify`: describe the photos in French when the interface is French

- **Priority**: Medium
- **Batch**: classify
- **Depends**: —
- **Files**: `src/media_hygiene/classify/ai/templates/describe.txt`, `src/media_hygiene/classify/ai/prompts.py`, `src/media_hygiene/classify/ai/describe.py`, `src/media_hygiene/index/`, `documentation/en/sort/08-subjects-from-a-local-model.md`, `documentation/fr/sort/08-subjects-from-a-local-model.md`

## Context

`describe.txt` says "Answer in English" whatever the locale; the docs explain it ("the model
reads them, you do not have to"). On the first real `mh classify --sample 50` (review 0056,
2026-10-12) the maintainer, with `locale = "fr"`, read English descriptions in the table and
took it for a bug. Decided: describe in French when the interface is French.

Cost measured on 2026-10-10 (40 real photos, `qwen3.8:27b`): 1.9 s per photo in English, 2.5 s
in French (desc + tags); on 2026-10-12 `classify` measured 2.1 s describe + 0.2 s map.

## What to do

1. `describe.txt` takes the answer language from the interface (`{language}` placeholder, or one
   template per language as `tags_en.txt` / `tags_fr.txt` do).
2. The cache (decided 2026-10-13): the language is part of a description's cache identity. A
   description in another language counts as missing and is described again (about 128 English
   descriptions on the maintainer's machine: ~5 min). Old cache rows without a language are
   English. The estimate and `--sample` follow from "missing" as today.
3. The mapping prompt (`map.txt`) states that descriptions may be in English or French.
4. Measure again `--sample 20` in French, then update the time figures and remove the
   "descriptions are in English" sentence of `sort/08-…` (en + fr).

## Explicit NON-goals

- Category definitions (0124), the subject console lines (0114).

## Acceptance

- `locale = "fr"`: new descriptions in French (test with the fake model server: the prompt asks
  for French).
- Under `locale = "fr"`, a cached English description is described again in French (test);
  under `en`, nothing is redone.

## Status — PARTIAL (2026-10-13)

### Done
- One describe prompt per language, like `tags`: `describe_en.txt` (the former `describe.txt`,
  byte for byte, so existing English cache rows keep their version and stay valid under `en`)
  and `describe_fr.txt`. `SubjectStep` reads `active_locale()`; the prompt's digest (part of the
  cache identity) differs per language, so under `fr` an English description counts as missing
  and is described again; under `en` nothing is redone.
- `map.txt` says the descriptions may be in English or French.
- Docs en + fr `sort/08-…`: the "descriptions are in English" sentence replaced by "in the
  interface language; switching it describes again"; the French sample table shows a French
  description.
- Tests: `tests/unit/test_subject_prompts.py`,
  `tests/integration/subjects/test_classify_subjects_language.py`.

### Not done
- Step 4: measure `--sample 20` in French on the real collection and update the time figures of
  `sort/08-…` (the console example still shows 3.6 s per photo).
  **Reason:** needs the maintainer's photos and Ollama.
- Note: a photo `tags` already described is still reused as is (its sentence is in the `[tags]`
  language, not necessarily the interface's): the mapping prompt accepts both languages. Not
  changed, to keep "a photo is sent to the model once".
