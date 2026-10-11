# 0082 — Tags: re-run the 40-photo benchmark with the fixed prompt

- **Priority**: Medium
- **Batch**: tags
- **Depends**: —
- **Files**: `src/media_hygiene/classify/ai/templates/tags_fr.txt`, `src/media_hygiene/classify/ai/templates/tags_en.txt`, `documentation/en/reference-tags.md`, `documentation/fr/reference-tags.md`

## Context

TODO 0072 (closed) measured prompt C on 40 real photos on 2026-10-10: 2.5 s median, but some
relationship words ("mother", "grandfather"), indented JSON (14–36 % of the output tokens spent
on whitespace) and phrases split into single words. The shipped prompts `tags_fr.txt` and
`tags_en.txt` fix these (people = adult/child/baby/group only, whole phrases, one-line JSON,
`maxItems: 10`, `num_predict` 240). Nobody has checked them yet: Ollama was not reachable during
the night run, so only `tests/support/fake_ollama.py` answered.

Reference setup of 2026-10-10: 40 photos, each from a different folder (2004–2022), 768 px,
`qwen3.8:27b-mtp-q4_K_M` on Ollama, `think: false`, temperature 0, the GPU to itself (another
model sharing it made 11 calls of 120 take 10–30 s).

## Steps

- [ ] By hand (the maintainer, on the real collection, read-only mount): `[tags] language =
  "fr"` and the model in `[classify.ai]`, then `mh tags --sample 40`, the GPU free.
- [ ] Read the table photo by photo: no relationship word nor name, one-line answers, phrases
  kept whole, no stop word left (`sol`, `mur`, `photo`…).
- [ ] Note the median time and the median output tokens here, next to the 2.5 s / 94 tokens of
  2026-10-10, and the estimate of a full run.
- [ ] If a word slips through: fix the prompt, or add it to the default `stop_words`, then
  rerun. Unit tests of `test_tag_vision.py` updated with the real answer that failed.
- [ ] Docs en/fr `reference-tags.md`: the measured time per photo, if it differs.

## Acceptance

- 40 real answers read, no relationship word, the measured times written in this TODO.
