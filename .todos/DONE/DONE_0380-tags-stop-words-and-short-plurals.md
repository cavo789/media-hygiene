# 0380 — Tags: more default stop words, and the short plurals inside phrases

- **Priority**: Low
- **Batch**: tags
- **Depends**: —
- **Files**: `src/media_hygiene/config/tags_settings.py`, `src/media_hygiene/tags/plurals.py`, `src/media_hygiene/config/templates/config.toml.j2`, `tests/unit/test_tag_normalize.py`, `documentation/en/reference-tags.md`, `documentation/fr/reference-tags.md`

## Context

On 2026-10-25 the maintainer had run `mh tags` for a few hours on `C:\Photos`. Claude
checked the answers in a copy of the index (volume `media-hygiene-cache`, read-only). Figures
below are **measured** on that copy: 3,138 answers from the current `tags_fr` prompt
(`ca86ddecff4f`), `qwen3.8:27b-mtp-q4_K_M`, and 2,743 photos already had `vision` tags.

- Answers follow the prompt: no relationship word, 99 % have 7 to 10 tags, every answer
  parsed, 2.5 % of sentences are over 25 words (32 at most), 2.9 s median per photo
  (p90 3.2 s).
- Accuracy, checked by eye on 12 random photos: 11 right, several precise (Egyptian
  sarcophagi, a falcon, the date printed on a 2004 photo). One factual error: carved fauns
  in Mechelen were called "skeletal figures", tagged `squelette`. One drift: the sentence
  was right ("three children on a bench"), but its tags lost `enfant` and switched to
  English (`sneakers`, `concrete`, `trash can`). English tags are rare, about 5 photos.
- **The prompt stays.** Changing it would describe everything again, about 2.5 h for the
  photos done so far (**estimated**: 3,138 × 2.9 s). Everything below changes the
  normalization only. Each `mh tags` run rebuilds the tags of every cached answer
  (`TagStep.derive`), so a fix applies to old answers too, without calling the model.

These figures also answer the checks of `BLOCKED_0082` (benchmark of the fixed prompt) on
far more than 40 photos.

## What to change

1. **Default stop words** (`STOP_WORDS`). Add words that say nothing about the photo itself:
   `photo floue`, `flou`, `photographie`, `ambiance`, `blurry photo`, `photograph`, `blur`.
   Measured counts of the French ones: `photo floue` 14, `flou` 13, `photographie` 7.
   `photo`, `image` and `scène` are already in the list.
   Decide whether to add `adulte` / `adult`. It is on 1,247 of 3,138 photos (40 %), often
   for someone in the background, but it still lets a search tell `enfant` from `adulte`.
   Proposal: keep it, and say why in a comment.
2. **Short plurals inside a phrase.** `clean` singularizes each word, but `singular` leaves
   words under 4 letters as they are (`_MIN_LENGTH`, so that `des`, `bus` and `gas` stay).
   As a result, `arbres nus` becomes `arbre nus` (measured: 1 tag). Add the short French
   adjective plurals (`nus`, `bas`?) to an explicit list, or make the adjective agree with the
   noun. Keep `bus` unchanged. Add one test per case to `test_tag_normalize.py`.
3. **`config.toml` template and docs.** Any `stop_words` list in `config.toml` replaces the
   built-in one (already documented in `reference-tags.md`). The commented example in
   `config.toml.j2` should list the full default set, so that a user who adds one word does
   not silently lose the others. Update both languages.

## Not in scope

- `femme` / `homme` (50 tags, measured) despite the "adult/child/baby/group" rule. These are
  not relationship words: leave them, unless the maintainer says otherwise.
- Generic words (`extérieur` is already a stop word; `nature`, `ciel bleu`, `végétation`):
  they help a search.
