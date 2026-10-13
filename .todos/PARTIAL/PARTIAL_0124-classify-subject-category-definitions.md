# 0124 — `subject` rule: a definition per category, and "À la maison" instead of "Maison et travaux"

- **Priority**: High — the categories chosen by the model were mostly wrong on the real collection
- **Batch**: classify
- **Depends**: —
- **Files**: `src/media_hygiene/classify/ai/templates/map.txt`, `src/media_hygiene/classify/ai/mapping.py`, `src/media_hygiene/classify/rules/building.py`, `src/media_hygiene/config/classify_settings.py`, `src/media_hygiene/config/templates/config.toml.j2`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/sort/08-subjects-from-a-local-model.md`, `documentation/fr/sort/08-subjects-from-a-local-model.md`

## Context

First real `mh classify --sample 50` (review 0056, 2026-10-12; 7 categories: Vacances et sorties,
Fêtes, École, Sport et loisirs, Maison et travaux, Animaux, Nature et paysages). The maintainer
found the **descriptions very good** and the **categories weak**: 7 wrong of the 10 categorised
photos checked —

- five home scenes (a man holding a girl, a girl with her teddy bear, a sofa, a Wii game, the
  patio) → "Maison et travaux": nothing to do with works;
- a family meal at the grandparents' → "Vacances et sorties";
- two girls with Santa hats in a September garden → "Fêtes".

Cause: `map.txt` gives the model the category **names only** and asks for "the one that fits
best": a name containing "Maison" draws every indoor scene, "sorties" draws every meal.
Decided: a definition per category written by the user; no `bge-m3` vectors (they would keep the
same word confusion, less explainably).

## What to do

1. `categories` entries accept `"Name = definition"`: the text before ` = ` is the category
   (folder), the rest is sent to the mapping model only. Plain names keep working.
2. `map.txt` lists `Name: definition` lines and asks to choose "none" rather than stretch a
   category; keep the JSON answer format.
3. Default examples (`config.toml.j2`, both catalogues) get definitions, and "Home and works" /
   "Maison et travaux" becomes "At home" / "À la maison" ("everyday life at home: games, meals,
   children, sofa"); "Fêtes" is defined as real celebrations (birthdays, Christmas, communions,
   weddings), not a costume alone.
4. Docs en + fr (`sort/08-…`): why definitions matter, with the real examples above (no photo).
5. Re-run `mh classify --sample 50` with the maintainer (same seed or same photos if `--sample`
   allows; otherwise a fresh 50) and note the new correct count in the closing status.

## Explicit NON-goals

- Embeddings / CLIP (rejected), French descriptions (0123), console wording (0114).

## Acceptance

- Tests: a `Name = definition` entry maps to the folder `Name`; the prompt sent to the fake
  model server holds the definition; plain names unchanged.
- The default config shows definitions and "À la maison".

## Status — PARTIAL (2026-10-13)

### Done
- `categories` entries accept `"Name = definition"` (`classify/ai/categories.py`): the name is
  the folder and the only value the model may answer (JSON `enum`); the definition goes to the
  mapping prompt only; the mapping cache key holds the whole entry, so a changed definition maps
  again (descriptions are kept). Validation checks the name only (`config/classify_rules.py`).
- `map.txt` lists `Name: definition`, asks for "none" rather than stretching a category; the
  mapping question moved to `classify/ai/map_prompt.py` (`prompts.py` would pass 200 lines).
- Default example (`config.toml.j2`, both catalogues): definitions, "At home" / "À la maison",
  "Parties" / "Fêtes" added and defined as real celebrations. Definitions kept short: the
  generated `config.toml` must stay within 88 columns (`tests/unit/test_config.py`).
- Docs en + fr `sort/08-…`: "Define each category" with the real examples (no photo); `06-…`
  example list says "At home".
- Tests: `tests/unit/test_subject_prompts.py`, `tests/unit/test_subject_rule.py`,
  `tests/integration/subjects/test_classify_subjects_language.py`.

### Not done
- Step 5: re-run `mh classify --sample 50` on the real collection and note the new correct count.
  **Reason:** needs the maintainer's photos and Ollama (autonomous session); the measure belongs
  with 0104's hands-on measurements.
