# 0104 — Maintainer's hands-on measurements with the real photos (Ollama, faces, search)

- **Priority**: Medium — several BLOCKED TODOs wait on these numbers
- **Batch**: review
- **Depends**: —
- **Files**: `.todos/BLOCKED/BLOCKED_0082-tags-benchmark-fixed-prompt.md`, `.todos/BLOCKED/BLOCKED_0084-search-measure-then-vectors.md`, `.todos/PARTIAL/PARTIAL_0083-tags-inherit-near-videos-classify-reuse.md`

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

## Acceptance

- Every section done, its numbers written in the TODO it unblocks; this file then moves to
  `DONE/`.
