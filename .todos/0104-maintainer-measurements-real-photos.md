# 0104 — Maintainer's hands-on measurements with the real photos (Ollama, faces, search)

- **Priority**: Medium — several BLOCKED TODOs wait on these numbers
- **Batch**: review
- **Depends**: —
- **Files**: `.todos/BLOCKED/BLOCKED_0082-tags-benchmark-fixed-prompt.md`, `.todos/BLOCKED/BLOCKED_0084-search-measure-then-vectors.md`, `.todos/PARTIAL/PARTIAL_0083-tags-inherit-near-videos-classify-reuse.md`, `.todos/BLOCKED/BLOCKED_0090-people-model-choice.md`

## Context

Some TODOs need runs that only the maintainer can do: they read the real collection
(`C:\Photos`, mounted read-only) and load the local vision model (Ollama, GPU). An unattended
agent must neither read those photos nor load the GPU (the PC crashes under heavy load). This
file gathers what to run, step by step; each section names the TODO its numbers unblock.

## 1. Tags benchmark, 40 photos (unblocks 0082, then 0084 and part of 0083)

About 2 minutes of model time.

1. `config.toml`: `[tags] language = "fr"`, `[classify.ai] model = "qwen3.8:27b-mtp-q4_K_M"`.
   Free the GPU first: `ollama ps` lists nothing.
2. PowerShell: `mh tags --path "C:\Photos" --sample 40`.
3. Read the table line by line: no kinship word nor first name, expressions kept whole, no empty
   word (`sol`, `mur`, `photo`…).
4. Note the median of the "Seconds" column (2.5 s on 2026-10-10) and the estimate of a full run
   printed under the table.
5. A word that should not pass: add it to `[tags] stop_words`, or fix `tags_fr.txt` /
   `tags_en.txt`, then run again; copy the faulty answer into `tests/unit/test_tag_vision.py`.
6. Give the numbers to Claude (or write them in `BLOCKED_0082-…`): it closes 0082, updates
   `reference-tags.md` (en + fr) if the time per photo differs, and unblocks 0084.

Decided in review (2026-10-12): no output-token column in `tags --sample`; the time per photo
decides.

## 2. Twenty real searches (unblocks 0084) — after section 1

1. One night of `tags`: `mh tags --path "C:\Photos" --yes` (`--yes` skips the question).
2. Twenty searches you would really type, with `mh search <words>` or the page: events
   (`anniversaire Léa`), places (`Durbuy`, `mer`), objects (`gâteau`, `vélo`), seasons
   (`neige 2010`). Since 0092 the words of the file names count too.
3. For each: the photos found, and those expected but missed (open the folder). Class each miss:
   plural or spelling (→ `tags/plurals.py`), empty word, synonym (`mer` / `bord de mer`), or
   truly about meaning (→ vectors).
4. Write the table in `BLOCKED_0084-…`. Build the `bge-m3` vectors (the TODO's plan) only if
   misses about meaning dominate.

Decided in review (2026-10-12): if the misses are mostly synonyms, a short synonym list in
`[tags]` rather than vectors (simpler, explainable).

## 3. Videos, classify reusing tags, cost of near duplicates (0083)

1. `mh tags --path "C:\Photos\Vidéos" --sample 5`: videos appear in the table, their words are
   plausible (one frame at the middle of each video; if poorly described, 0083 suggests three
   frames at 30/50/70 %).
2. On a folder `mh tags` already went through: `mh classify` with a `subject` rule says
   "0 photos described" for those photos, and the categories hold (the French answers of `tags`
   are matched to the categories by the text model).
3. A full `mh audit` with the cache: note how long the "near duplicates" step takes. Under one
   minute: `tags` runs that search itself so near-duplicate groups share one description (the
   remainder of 0083); otherwise it reads the groups of the last audit report.

## 4. SFace against ArcFace (unblocks 0090)

Pick a year with many children (same children at different ages, look-alike siblings): that is
where ArcFace should make the difference.

1. SFace, the tool: `mh people --path "C:\Photos\<year>"`, look at the page.
2. ArcFace, outside the image: the measurement script is kept **outside the repository**
   (InsightFace's `buffalo_l` weights are for non-commercial use only), in the maintainer's
   private plans folder. From WSL, in a throwaway Python 3.12 environment (`insightface`
   compiles at install and may fail on a newer Python): `uv venv --python 3.12 /tmp/arcface`,
   `uv pip install insightface onnxruntime opencv-python-headless numpy pillow pillow-heif`,
   then run the script on `/mnt/c/Photos/<year>` with `--threshold 0.40`, then `0.35` and `0.45`
   (ArcFace's similarity scale is not SFace's). It writes an HTML page of the groups.
3. On each page count: groups mixing two people, people split into several groups, time per
   photo.
4. Afterwards: `rm -rf /tmp/arcface ~/.insightface`.

Decided in review (2026-10-12): if ArcFace is only slightly better, drop it and keep SFace alone
(a non-commercial licence and ≈ 300 MB of weights are only worth a clear gain).

## 5. Try the people page and the names (0091, never run in a real browser)

1. `mh people`: name a group, name a second one the same (merge), remove a face (×), ignore a
   group (`i`), confirm a suggestion (`y`); open `config.toml`: comments kept,
   `[[people.person]]` written.
2. Run `people` again: the names are still there, `Named: …` in the console.
3. `mh search Chloé montagne`, `mh search person:chloe`, `mh search person:Unknown` (one line
   says nobody is named so).
4. `mh people --forget` in a terminal: answer no, then yes (read back from `config.toml`).
5. Keys `x`, `i`, `y`, ×: keep them or ask Claude to change them after this try.
6. The `person` rule (0095), once "Chloé" is named: add
   `[[classify.rules]]` `name = "With Chloé"`, `match = "person"`, `names = ["Chloé"]`,
   `category = "People/Chloé"`, then `mh classify`: the rule in the *Why* table and the
   *Reason* column of the workbook. Then `names = ["Manon"]` (nobody so named): `classify` stops
   and names the rule and the people named. Then `min_share = 50` and `all = true` with two
   names: fewer events taken. Decided in review (2026-10-12): `min_share` 10 % by default, to
   revisit after this try.

## Acceptance

- Every section done, its numbers written in the TODO it unblocks; this file then moves to
  `DONE/`.
