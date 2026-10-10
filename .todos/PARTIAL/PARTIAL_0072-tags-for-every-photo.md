# 0072 — Tags: one searchable label layer, fed by the vision model, folders, dates and places

- **Priority**: Medium — the base of 0073 (search) and 0074 (XMP sidecars); measured on the real collection
- **Batch**: tags
- **Depends**: —
- **Files**: `src/media_hygiene/tags/` (new: producers, normalize, describe run), `src/media_hygiene/index/schema.py`, `src/media_hygiene/index/` (new `tag_rows.py`), `src/media_hygiene/index/pruning.py`, `src/media_hygiene/classify/ai/prompts.py`, `src/media_hygiene/classify/ai/templates/`, `src/media_hygiene/cli/` (new `cmd_tags.py`), `src/media_hygiene/config/settings.py`, `src/media_hygiene/config/templates/config.toml.j2`, `src/media_hygiene/report/` (inventory column), `documentation/en/`, `documentation/fr/`

## Context

The maintainer wants (2026-10-10) to find photos by what they show ("Durbuy ours",
"anniversaire gâteau", "neige") and to keep those words with the photos, outside any
application. Ideas came from a Gemini answer: Ollama describes each photo, tags are written
into EXIF/IPTC, and a SQLite FTS5 index feeds a search page.

Already built (0029, PARTIAL): the Ollama client, the describe step (768 px JPEG from the
process pool, RAW previews, JSON schema, `think: false`), the `descriptions` table (schema 4)
keyed by path + size + mtime + model + prompt digest, resumable, following `sort` moves. It
only serves `classify`, on a few samples per event.

**Not written into the photo files.** Rewriting a JPEG changes its bytes: its SHA-256, its
mtime, the index rows, and two identical copies stop being identical when only one is tagged.
That breaks the core of this tool (byte-exact duplicates), risks the originals and needs
ExifTool (Perl) in the image. Portable tags go to XMP sidecars instead (0074).

### Benchmark (2026-10-10, real collection, read-only)

- **Setup**: 40 photos, each from a different folder (2004–2022), drawn at random among
  ≈ 50,000 JPEG/PNG/HEIC outside `#recycle`; 768 px; `qwen3.8:27b-mtp-q4_K_M` on Ollama 0.34.3;
  `think: false`, temperature 0, JSON schema; three prompts per photo.
- **Prompts**: A = current `describe.txt` (English sentence + 5 tags); B = French tags only
  (5–10); C = French sentence (≤ 25 words) + 5–10 French tags.

| Prompt | Median | Output tokens (median) |
|---|---|---|
| A, English sentence + tags | 1.9 s | 66 |
| B, French tags only | 1.9 s | 72 |
| C, French sentence + tags | 2.5 s | 94 |

- Time ≈ 0.73 s to read the image (≈ 525 prompt tokens) + output at ≈ 60 tokens/s. Faster
  than the 3.5 s of 2026-09-28.
- 11 calls of 120 took 10–30 s: another client (`code-quality`, 17 GB) shared the 24 GB GPU
  and Ollama swapped models. A long run needs the GPU to itself.
- Ollama returned **indented JSON**: whitespace was 14–36 % of the output tokens.
- Estimate: ≈ 50,000 photos × ≈ 2.2 s ≈ 30 h (3–4 nights), less when only one photo per burst
  series / near-duplicate group is described.

Quality, read photo by photo against the folder names:
- **Good**: wedding cake, birthdays (candles, cake), snowman, ice rink, ponies with helmets,
  mountain hike, Gothic cathedral, rabbit in a cage, cat, baby on a play mat. Visible text is
  read ("Paris-Brest" on a mural, "Vivons Sport" on a banner).
- **Occasions missed** (as in 0029): Easter 2007 → "cadeau" (prompt B: "pique-nique, été" in
  April); Christmas 2006 → "jeu, musique"; New Year → "fête".
- **Places unknown**: Sicily, Morzine, Durbuy, Aachen, Rocamadour → "cathédrale", "château".
  The folder names knew every one of them.
- **Invented relationships**: "une mère et sa fille", "une grand-mère et sa petite-fille",
  "sa sœur".
- **Wrong identification**: a chalet lounge → "salle de réunion"; one animal → "furet" or
  "blaireau"; a cat → "mâtin"; a selfie with a beard filter → "jeune femme".
- **Unstable words**: singular not respected ("bougie" / "bougies", "fleur" / "fleurs"),
  "salle à manger" split into "salle", "à", "manger"; typos ("poneaux", "médieval").
- **C is the most useful for search**: the sentence adds words the tags lack ("patinoire",
  "nuptial", "parc d'attractions"). B is noisier ("sol", "mur", "rideau", "chaussette"). A is
  the most accurate, but English does not suit a French search nor French sidecars.

**Conclusion**: the model sees scenes and objects well, never occasions nor places. Its words
are only useful next to the folder names, dates and places this tool already knows.

## Proposal

### One label layer, several producers

A `tags` table in the index (schema 6): file identity (path, size, mtime), `source`
(`vision`, `folder`, `date`, `place`, later `person` from 0058), `value`, `model` / version
when it applies. Pruned and moved with the file like the other rows. Each producer is
recomputed independently; nothing is stored as truth that can be derived again in seconds.

| Source | Words | Cost |
|---|---|---|
| `vision` | sentence + tags from Ollama (prompt C, fixed below) | ≈ 2.2 s per photo, nights |
| `folder` | words of the folder names, minus generic ones (`DCIM`, `Photos`, months, years) — reuse the generic-folder list of `KeepPolicy` and `classify` | seconds |
| `date` | year, month, season, fixed holidays and the calendar of 0035 (Noël, Pâques, Saint-Nicolas…) | seconds |
| `place` | `[[classify.places]]` names, GeoNames town of the GPS position (`geo/`) | seconds |

### The vision producer

- **Prompt C**, in `templates/` (French by default, the language follows `[tags] language`),
  with the measured fixes:
  - no relationship words: "adult, child, baby, group", never "mother", "sister";
  - multi-word tags kept whole ("salle à manger");
  - one-line JSON asked for; if Ollama still indents, nothing to do but count it.
- **Normalization after the answer** (pure function, unit-tested): lower case, trimmed,
  singular for simple French plurals, duplicates removed, tags of one or two letters dropped,
  a stop list (`sol`, `mur`, `intérieur`, `extérieur`…) in config.
- **Reuse the 0029 machinery**: client, previews, cache table (a new prompt digest, so the
  `classify` descriptions stay valid), resume after Ctrl+C, time estimate and confirmation
  above `confirm_above`.
- **Describe less**: one photo per burst series and per near-duplicate group (`plan/similar`),
  the others inherit its `vision` tags; files below `min_edge` and videos skipped (videos:
  later, on one keyframe of `video_prints`).
- **Order**: newest folders first, or a `--path` filter, so the first night is already useful.

### Command

`media-hygiene tags`:
- `tags --sample N`: N random photos, a table of sentence + tags + seconds, the estimate of a
  full run;
- `tags` (or `tags --path …`): computes the cheap producers, then describes what is missing;
  prints count and estimated time first, read-only on the data mounts 🔒;
- `tags --no-describe`: cheap producers only, seconds;
- the summary line says how many photos have `vision` tags and how many are left.

### Uses inside the tool

- a "tags" column in `inventory.xlsx` / `.csv`;
- `classify` may read `vision` tags instead of describing again when the model and prompt
  match (later; do not merge the two prompts now).

## Acceptance

- [ ] Fake Ollama server tests (reuse the 0029 one): describe, normalize, inherit within a
      burst series, resume, `--no-describe`.
- [ ] Unit tests of the cheap producers (folder words, generic folders dropped, holidays,
      places) on synthetic paths.
- [ ] Re-run the 40-photo benchmark with the fixed prompt: no relationship word, median time
      noted here.
- [ ] Off by default: an audit never calls Ollama.
- [ ] Documentation en + fr (time estimate, GPU shared with other models, privacy: images go to
      the configured URL only); `.po` translated.

## Status — PARTIAL (2026-10-11)

### Done
- `tags` table in the index (schema 6: path, size, mtime, source, value, model; index on
  `value`), forgotten and moved with the file (`index/schema.py` `FORGET`/`MOVE`);
  `index/tag_rows.py` (`TagStore.replace` per source, `of`, `counts`, `tags_reader`).
- Sources (`tags/models.py` `TagSource`): `folder`, `date`, `place`, `vision`, plus `caption`
  (the model's sentence, kept whole for the search of 0073). Cheap sources recomputed at every
  run; model sources derived at every run from the `descriptions` cache.
- Cheap producers (`tags/producers.py`, `tags/dates.py`, `tags/vocabulary.py`,
  `tags/context.py`): folder words through `classify`'s `FolderRules` (generic folders of
  `[keep]` and `[classify]`, band folders, date folders), months and linking words dropped;
  year, month, season (southern hemisphere turned), fixed holidays, Easter (computus), the
  user's `calendar` and `date_range` rules, the folder year when no date; personal places and
  the GeoNames town and country within `[tags] town_km`.
- Vision producer (`tags/vision.py`, `classify/ai/templates/tags_fr.txt`, `tags_en.txt`):
  prompt C with the measured fixes (no relationship words, phrases whole, one-line JSON,
  `maxItems` 10), its own prompt digest; normalization (`tags/normalize.py`,
  `tags/plurals.py`): lower case, trimmed, simple French/English singulars, ≤ 2 letters and
  `[tags] stop_words` dropped, duplicates removed. The raw answer is cached; normalization runs
  when tags are derived (a new stop word needs no model call).
- Reuse of the 0029 machinery: `DescribeDeps` takes a `Question` (default: classify's), so
  client, previews, cache, resume after Ctrl+C, time estimate and `confirm_above` are shared.
- Describe less (`tags/selection.py`): one photo per set of identical files (SHA-256) and per
  burst series (`plan.bursts`, the sharpest shot); videos and photos below `min_edge` skipped;
  newest first; `--path`.
- `media-hygiene tags` (`cli/cmd_tags.py`, `cli/tags_flow.py`, `services/tags.py`,
  `services/tag_describe.py`, `services/tag_files.py`, `console/tags_view.py`): `--path`,
  `--no-describe`, `--sample N`, `--yes`; read-only marker and launcher (`READ_ONLY_COMMANDS`,
  `PHOTO_READERS`); count and estimate printed first; summary of photos with the model's
  words and those left; next step `inventory`.
- `[tags]` settings (`config/tags_settings.py`, `config.toml.j2`): `language` (empty: the
  interface's), `stop_words`, `town_km`. The model stays in `[classify.ai]`.
- "Tags" column (last) in `inventory.xlsx` / `.csv` (caption left out).
- Off by default: no model, nothing sent; an audit never calls the model (asserted in the
  tests' fixture).
- Tests: unit (`test_tag_normalize.py`, `test_tag_producers.py`, `test_tag_rows.py`,
  `test_tag_vision.py`) and fake-Ollama integration (`tests/integration/tags/`: describe,
  inherit in a burst and from a copy, resume, `--no-describe`, `--sample`, confirmation,
  `--path`, no model, model without vision, no index, inventory column).
- Documentation en + fr (`reference-tags.md`, README, commands, inventory); `.po` translated.

### Not done
- Inherit within near-duplicate groups (`plan/near`): only identical copies and burst series
  share a description.
  **Reason:** the near-duplicate search is heavier (multi-index hashing over the whole
  index) and its groups depend on review decisions; left for a follow-up once the cost on the
  real collection is measured.
- Re-run the 40-photo benchmark with the fixed prompt (no relationship word, median time).
  **Reason:** the vision model (Ollama) was not reachable during this session; only fake
  servers were used. To do by hand: `tags --sample 40` with `[tags] language = "fr"`.
- Videos on one keyframe of `video_prints`, and `classify` reading the `vision` tags instead
  of describing again: both marked "later" in the proposal.
  **Reason:** out of scope of this TODO by its own text.
- `status` does not mention tags yet (counts per source and photos left to describe).
  **Reason:** not asked by the TODO; natural to add with 0073 (search), which reads the same
  counts.
- Help captures of `documentation/*/reference-commands.md` (`<!-- capture: … -->`) still lack
  `tags`.
  **Reason:** `docs_screenshots` needs a Docker build, not run during the night session.
