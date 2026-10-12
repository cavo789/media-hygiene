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
2. The cache: a description is stored with its language; a French run reuses an English
   description rather than paying again (the mapping step reads either language) — the table of
   `--sample` then shows it as is. Decide and write down whether `--sample` redraws photos whose
   cached description is in the other language (preferred: no).
3. The mapping prompt (`map.txt`) states that descriptions may be in English or French.
4. Measure again `--sample 20` in French, then update the time figures and remove the
   "descriptions are in English" sentence of `sort/08-…` (en + fr).

## Explicit NON-goals

- Category definitions (0124), the subject console lines (0114).

## Acceptance

- `locale = "fr"`: new descriptions in French (test with the fake model server: the prompt asks
  for French).
- Cached English descriptions still map; no re-describe.
