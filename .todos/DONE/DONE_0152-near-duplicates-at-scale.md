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

## Status — DONE (2026-10-14)

### Done
- Item 1, benchmark (devcontainer, synthetic clustered hashes: scenes of 1–30 shots 4–12 bits
  apart, 10 % near copies within 2 bits; `near_decisions` alone, one process):

  | Photos | before | after |
  |---|---|---|
  | 50,000 | 0.36 s | 0.10 s |
  | 100,000 | 0.97 s | 0.28 s |
  | 300,000 | 3.89 s | 1.17 s |

  Same decisions (4,585 / 9,165 / 27,409). The profile before: 5.5 million pair tests in
  Python; after: two `close_pairs` calls, what is left is `UnionFind.sets` (0.5 s at 300,000).
- Item 2: `plan/near_pairs.close_pairs`: per quarter, `argsort` of the 16-bit keys, pairs of
  equal keys by offset, both distances with `np.bitwise_count`, colours in bulk (NaN =
  unknown). `near._clusters` links those pairs. `tests/unit/test_near_pairs.py` proves the
  same pairs as the one-by-one reference on five random sets, colours known or not; the
  near-duplicate, burst and similar tests pass unchanged.
- Item 3 not needed: with item 2 the second `find_similar` run costs about a second at
  300,000 photos.

### Not done
- The `near duplicates` stage of the maintainer's warm audit, before and after.
  **Reason:** needs the real collection and an image build (Docker Desktop).
- Item 4 for `near_video._clusters` (videos sorted by duration, each compared with the next
  ones of about the same length): many clips of one length (messaging videos) would compare
  each with each. **Reason:** not measured as slow; revive if the `same streams`/`near
  duplicates` stage grows on a collection with thousands of short clips.

## Inbox (2026-10-14)

- Item 4 (`near_video._clusters` with numpy) dropped: not measured as slow. Only the maintainer's measurement (`mh-measure.ps1` step 6) remains.

## Windows measurement (2026-10-14)

Measured by the maintainer on 2026-10-14 with `tests/measure/mh-measure.ps1` (Windows, Docker
Desktop, image built from `main`; runs `measures-20261014-2116` and `-2125`), warm audit of `C:\Photos` (52,054 files, nothing changed): `near duplicates` 0.9 s
of a 3 s audit (4.0 s wall time); `colours` and `same streams` 0.0 s. Test folder of 12,000
photos: 0.2 s. Only the "after" was measured (no image from before c0cf34f rebuilt); the
whole warm audit stays at the 3–4 s measured before. Closed on the "after".
