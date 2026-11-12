# The pages' speed budget (0678)

What each read route of the pages costs the home server as the library grows, on a
synthetic index (`tests/measure/pages/library.py`: no picture, the real schema written
by the index's own writers; shaped like the maintainer's library measured 2026-10-17:
2.9 % videos, 9 % undated, 1.3 % with GPS, 0.52 face per file, folders of 40 files,
two tenths of them a camera's dump not sorted yet).

## Method

- **Measured** 2026-11-11 in the devcontainer (Intel i9-14900K, 16 threads seen, 47 GB,
  WSL2), `nice -n 19`, `PYTHON_CPU_COUNT=4`, one size at a time:
  `python -m tests.measure.pages.bench <files> <folder> --out <file>.json`.
- The bench starts `home` in its process as `mh` does and sends each route through the
  server's router (no socket: the server's work only, not the browser's). The warm-up of
  the first clicks (0677) is **disabled**: the server's `ready` callback is never called.
- *Cold*: the first request of the route in a fresh process, routes in the table's order
  (the first route opening the index pays for those after it). *Warm*: median of the
  next 5. The index is copied afresh at each run (the people page writes its face
  groups into it).
- Peak memory (`ru_maxrss`): 362 MB at 10,000; 1,123 MB at 100,000 (the people page's
  face grouping); at 300,000, 244 MB for the light routes, 2,375 MB for folders, found
  events and places together.
- 300,000: the people page's first opening alone is estimated ≈ 250 s (× 9 from
  100,000: quadratic, 0693) — over the 3 minutes a run may take here, so the people
  routes are not run at that size; the other routes ran in two passes (`--skip`).
- Budget: `max(100, warm × 1.5)` rounded up to 10 ms — the figure the helper refuses to
  go past; `bench_pages` also fails on a warm time grown by more than 30 % against this
  table (routes under 5 ms excepted: their spread is larger). The target of 0678, warm
  ≤ 100 ms at 100,000, is missed by the rows whose budget is above 100 there.

## Table

| Route | Files | Cold ms | Warm ms | Budget ms |
|---|---:|---:|---:|---:|
| home state | 10,000 | 346.0 | 13.7 | 100 |
| home state | 100,000 | 428.2 | 73.1 | 110 |
| home state | 300,000 | 594.7 | 201.3 | 310 |
| search: words | 10,000 | 420.7 | 11.5 | 100 |
| search: words | 100,000 | 1,266.3 | 16.8 | 100 |
| search: words | 300,000 | 3,176.1 | 28.1 | 100 |
| search: a period | 10,000 | 22.7 | 21.8 | 100 |
| search: a period | 100,000 | 119.7 | 120.2 | 190 |
| search: a period | 300,000 | 319.8 | 315.3 | 480 |
| search: a place | 10,000 | 12.9 | 12.5 | 100 |
| search: a place | 100,000 | 17.8 | 17.5 | 100 |
| search: a place | 300,000 | 28.8 | 29.4 | 100 |
| search: nothing typed | 10,000 | 19.0 | 18.9 | 100 |
| search: nothing typed | 100,000 | 68.0 | 66.7 | 110 |
| search: nothing typed | 300,000 | 172.6 | 166.6 | 250 |
| folders | 10,000 | 287.2 | 299.5 | 450 |
| folders | 100,000 | 2,991.9 | 2,955.7 | 4,440 |
| folders | 300,000 | 9,849.9 | 8,851.5 | 13,280 |
| events: a year | 10,000 | 11.4 | 11.1 | 100 |
| events: a year | 100,000 | 113.8 | 109.4 | 170 |
| events: a year | 300,000 | 348.6 | 330.5 | 500 |
| events: found in folders | 10,000 | 188.4 | 191.0 | 290 |
| events: found in folders | 100,000 | 1,822.8 | 1,827.1 | 2,750 |
| events: found in folders | 300,000 | 5,547.4 | 5,536.4 | 8,310 |
| people page | 10,000 | 961.1 | 338.9 | 510 |
| people page | 100,000 | 27,335.9 | 3,672.0 | 5,510 |
| people groups | 10,000 | 11.9 | 11.9 | 100 |
| people groups | 100,000 | 76.8 | 68.5 | 110 |
| places page (clusters built) | 10,000 | 817.7 | 469.6 | 710 |
| places page (clusters built) | 100,000 | 5,254.3 | 5,194.3 | 7,800 |
| places page (clusters built) | 300,000 | 14,495.6 | 14,759.8 | 22,140 |
| places clusters | 10,000 | 1.1 | 1.0 | 100 |
| places clusters | 100,000 | 7.7 | 1.8 | 100 |
| places clusters | 300,000 | 11.7 | 2.6 | 100 |
| albums | 10,000 | 0.8 | 0.1 | 100 |
| albums | 100,000 | 1.3 | 0.3 | 100 |
| albums | 300,000 | 0.9 | 0.2 | 100 |

## What grows faster than linearly

- The people page's first opening (face grouping, all pairs: 0.96 s → 27.3 s for ×10
  files, measured): 0693. After 0693 (only the faces above the threshold are kept, then
  cut to the closest; buffers reused): 13.5 s cold at 100,000 (measured 2026-11-12, load
  average 6–9 from other sessions; face grouping alone 24.4 s → 10.3 s). Still all pairs
  (the matrix product): the ≤ 5 s target needs an approximate search or float16.
- Everything else grows about linearly (×10 files: ×5 to ×12; ×3 files: ×2.6 to ×3.3,
  measured), but several routes are slow in absolute terms at 100,000: folders 3.0 s,
  places page 5.2 s (it reads every row of the index, facts parsed, for the 1.3 % with
  GPS: py-spy at 100,000, 72 % in `places_index.read_index`), found events 1.8 s, the
  people page again 3.7 s (a `stat` and a query per photo).

## Running it again

`bench_pages` (devcontainer helper; sizes as arguments, 10,000 and 100,000 by default)
builds each index once into `/tmp/media-hygiene/bench-pages`, runs the bench, then
`python -m tests.measure.pages.budget` compares with this table. After an accepted
change, replace the rows of this table with the new figures.
