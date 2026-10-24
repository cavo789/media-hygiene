# 0353 — `tags`: the model's words reach the search as each photo is described

- **Priority**: High
- **Batch**: search
- **Depends**: —
- **Files**: `src/media_hygiene/services/tags.py`, `src/media_hygiene/services/tag_derive.py`, `src/media_hygiene/services/tag_describe.py`, `src/media_hygiene/services/describing.py`, `src/media_hygiene/classify/ai/describe.py`, `src/media_hygiene/cli/tags_flow.py`, `src/media_hygiene/index/tag_rows.py`, `src/media_hygiene/search/fts.py`, `documentation/en/commands/tags.md`, `documentation/fr/commands/tags.md`, `documentation/en/commands/search.md`, `documentation/fr/commands/search.md`

## Context

Reported by the maintainer (2026-10-24): `mh tags` had been running for more than two hours,
over 2,700 photos described (about 2.7 s per photo, *measured* by the maintainer's own figures),
and `mh search` found nothing from the model.

Why: each answer of the model is committed at once in `descriptions`
(`classify/ai/describe.py:152` → `index/descriptions.py`, `put` then `commit`), but the `tags`
rows the search reads (`caption`, `vision`) are written by `TagStep.derive` only after
`describe_photos` returns (`cli/tags_flow.py:86-87`). During a run of hours, the search only
knows the folder, name, date and place words. Ctrl+C does write them (derive runs after a
stop), which nobody can guess.

The search page already notices a changed index at no cost (`search/fts.py`, `PRAGMA
data_version`, rebuilt in `_fresh`): rows written during the run would show at the next search.

## What to do

1. After each answer is stored, write the `caption` + `vision` tags of the photo described **and
   of every file it answers for** (`work.vision.answered_by`: its identical copies, the burst
   series it leads, its near group) in the same transaction as the description. A reverse map
   leader → files built once in `plan`. One code path with today's `derive` (same
   `vision_tags`, same `TagStore.replace(MODEL_SOURCES, …)` per file), so that the final
   `derive` becomes a check with nothing left to write for the photos of the run; it still
   writes the files whose answer came from the cache.
2. `services/tags.py` is at 200/200 lines (*measured*, `near_limit.sh`, 2026-10-24): the derive
   goes to a new `services/tag_derive.py`, the hook passed to `DescribeJob` (a callback, or a
   store that writes both), never a fourth parameter.
3. Concurrency (*to check*, not measured): the index is in rollback-journal mode (no
   `journal_mode` set). A search page reading while `tags` commits every 2.7 s:
   - can the writer get `database is locked`? Set or check a `busy_timeout` on both sides,
     keep the reader's transactions short; test with a reader holding a read lock;
   - the search's FTS rebuild after each `data_version` change: measure its cost for 100,000
     files (synthetic index) — if more than a few hundred ms, rebuild at most every N seconds
     during a search session (a named constant).
4. A run stopped hard (window closed, `docker stop`): every photo described before it has its
   tags (test: kill between two answers, then search).
5. Docs en + fr: `tags` page says the words are searchable as the run goes; `search` page says a
   photo described a moment ago shows at the next search. `docs_screenshots` to run if a
   console capture changes (say it, do not run it).

## Acceptance

- During a `tags` run, a search for a word of a photo just described finds it, with its copies
  and its burst series.
- After the run, the `tags` rows are identical to today's (equivalence test: same index, old
  end-of-run derive vs new as-it-goes writing).
- No `database is locked` with a search page open during the run (test).

## Gain

Today: zero model words in the search until the run ends — hours on a collection (2,700
photos ≈ 2 h at the maintainer's pace, *measured* by them; a full collection several times
more, *estimated*). After: each photo searchable about 2.7 s after it is described, and a
stopped or crashed run loses no searchable word.
