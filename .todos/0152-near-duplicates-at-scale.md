# 0152 — Near duplicates of 300,000+ photos: compare the candidate pairs with numpy

- **Priority**: Medium — the candidate pairs grow with the square of the collection: 1.5 s today for 52,000 files, an estimated 6–12 s for 300,000 and 1–2 min for a million, on every `audit`, `review`, `clean` and `crosscheck`
- **Batch**: near
- **Depends**: —
- **Files**: `src/media_hygiene/plan/near.py`, `src/media_hygiene/plan/likeness.py`, `src/media_hygiene/plan/union_find.py`, `src/media_hygiene/plan/near_video.py`, `src/media_hygiene/services/near_checks.py`, `tests/unit/test_near_decisions.py`, `tests/unit/test_similar.py`

## Context

Speed and cache review of 2026-10-14 (third pass). This is the revival condition of 0144
(UNNEEDED): "revisit if `near duplicates` passes ~10 s on a warm audit of a larger collection".
It is the only step of a warm audit that is pure Python, and its work grows faster than the
collection: `near._clusters` compares every pair of photos sharing a 16-bit quarter of their
pHash (`combinations` inside each bucket), and `checked_similar` runs `find_similar` twice
(before and after the colours).

Measured on 2026-10-14: the pHash of 3,000 photos drawn at random from `C:\Photos`, computed by
the image's own `inspect_image`, gives **612 candidate pairs** in the quarter buckets (the
largest bucket holds 6 photos). As long as the buckets keep that spread, the pairs grow with
the square of the number of photos:

| Photos | Candidate pairs (upper bound) |
|---|---|
| 52,000 | ≈ 0.2 M (the `near duplicates` stage: 1.5 s, both runs) |
| 300,000 | ≈ 6 M |
| 1,000,000 | ≈ 68 M |

An upper bound: real near duplicates and bursts add pairs in proportion, not as the square.
The bare pair test costs 84 ns in Python; inside `_clusters` (lookups by path, `_close`,
`same_colours`) it costs several times more. Hence ≈ 3–6 s per run at 300,000 photos, twice.

Not worth a compiler (0144): numpy already holds the tool, and `np.bitwise_count` (numpy ≥
2.0, a dependency already) counts the bits of 64-bit integers in bulk.

## What to do

1. Benchmark first, without real photos: `near_decisions` on synthetic `VisualFacts` of 50,000,
   100,000 and 300,000 photos whose hashes follow clusters (shots of one scene a few bits
   apart, near copies within 2 bits), timed before any change.
2. Vectorise `_clusters`: pHash, dHash and colour in numpy arrays; for each quarter, `argsort`
   the 16-bit keys and take the runs of equal keys; inside a run, XOR + `np.bitwise_count` on
   both hashes at once, colours compared in bulk; the pairs left go to `UnionFind` as today.
   Same links, so the same groups, keepers and rounds: the existing near-duplicate, burst and
   similar tests must pass unchanged.
3. Only then, if the two `find_similar` runs still show: run the first one with the colours
   the index already knows. Prove first, with a randomised test comparing both flows, that the
   findings stay identical; otherwise leave it.
4. Check the other loops at the same scale: `bursts.burst_series` (sorted by camera and moment,
   a window of `BURST_GAP_SECONDS`: linear) and `near_video._clusters` (sorted by duration: many
   videos of one length, such as short messaging clips, would compare each with each).

## Acceptance

- The near-duplicate and burst tests pass unchanged.
- The benchmark of item 1, before and after, in the commit message; the `near duplicates`
  stage of the maintainer's warm audit before and after.
