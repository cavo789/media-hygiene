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
