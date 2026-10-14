---
name: measure-before-ranking
description: Method to measure where time and memory really go before ranking or implementing a speed TODO — cold vs warm reads, isolating each cost, synthetic data for CPU, real data read-only for I/O, light machine load, profiles, equivalence tests for any optimisation, and how to label figures (measured vs estimated). Load before a speed review, before writing a performance TODO, and before closing one.
disable-model-invocation: false
---

# Measure before ranking

A speed review ranked on guesses gets re-ranked by the first figures (seen: a "High" TODO
became UNNEEDED once a warm audit measured 3–4 s). Measure first, cheaply, then decide.

## 1. Decide what to measure

- Name the user's case in numbers: how many files, how big, which storage (local disk, a
  network or VM share), first run or warm run. The bottleneck differs per case: a first run
  on a slow share is bound by reading, a warm run by bookkeeping, a large collection by
  anything that grows faster than linearly.
- List the steps the code runs for that case, and what each costs per item.

## 2. Measure each cost on its own

- **CPU**: synthetic data shaped like the real one (sizes, compressibility, structure — a
  phone photo is a 3–4 MB JPEG, an iPhone HEIC a grid of tiles). One process, best of N
  runs, `time.perf_counter` and `time.process_time` (CPU vs wall: threads and I/O show up).
- **I/O**: real files, mounted read-only (`--mount type=bind,source=…,target=…,readonly`;
  `-v` creates a missing folder). Cold vs warm: split the files in two halves, read each half
  cold once per method, swap the order; the host's cache warms whatever was read before.
  Measure 1, 4 and 16 readers: latency-bound storage scales with concurrency, a disk does not.
- **Per-call latency** (`stat`, open): one at a time, then in a thread pool; a language
  change never removes a syscall, concurrency does.
- **Memory**: `tracemalloc` peak per item for the structures held, and for the bookkeeping
  (one task or future per item is easily 1.5–5 KB).
- **Growth**: run at 3 sizes (e.g. 50k, 100k, 300k items); a profile (`cProfile`, sorted by
  `tottime`) at the largest shows what grows.
- **Scaling estimate from a sample**: count the work on a random sample (e.g. candidate
  pairs among 3,000 real items) and extrapolate as the algorithm grows (quadratic: × (N/n)²);
  say it is an upper bound when part of the work grows linearly.

## 3. Keep the machine usable

One heavy step at a time, `nice -n 19`, a CPU limit on containers (`--cpus 1–2`), short
runs. Long `docker run` from an agent: `-d`, then `docker wait`, then `docker logs`. Scripts
live in the scratchpad, never in the repository.

## 4. Before replacing code for speed

- Prove equivalence: a test comparing the new result with the old algorithm kept as a
  reference in the test (same pairs, same groups, same digests, on random inputs and edge
  cases: empty, one item, ties, identical copies).
- Measure before and after on the same data; write both in the commit message.
- Prefer, in order: doing less work (a cache, one read instead of two), concurrency on
  latency-bound I/O, vectorising (numpy) a pure-language loop, and only then a compiled
  extension or another language, and only for a step the profile shows.

## 5. Report

Every figure says **measured** (what, where, how) or **estimated** (from which measures).
Rank TODOs on these figures; write them in the TODO and in its closing status. A
measurement only the user can run (their machine, their files, a GPU) goes into a list for
them, with the exact command and what to paste back.
