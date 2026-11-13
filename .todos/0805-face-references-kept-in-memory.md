# 0805 — Face references kept in memory: a large view costs the same with 80,000 named faces

- **Priority**: High
- **Batch**: page-speed
- **Depends**: —
- **Files**: `src/media_hygiene/person/names.py`, `src/media_hygiene/person/lookup.py`, `src/media_hygiene/person/likeness.py`, `src/media_hygiene/person/finding.py`, `src/media_hygiene/people/known.py`, `src/media_hygiene/people/people_memo.py`, `tests/unit/test_person_names.py`, `tests/unit/`

Filed by the speed review of 2026-11-13. Principle set by the maintainer: **sorting must
be favoured, never punished** — the people files under `/config/people/` (above 1 MB
already) grow with every name given, and no page may get slower because of it.

## Context

0714's *who is on it* line of every photo opened large (`/person`, `/library`, the
people page) used to re-parse `config.toml` and the ~90 people files at each large view
(0.66–0.91 s measured 2026-11-12); `people_memo` now parses them again only when a file's
signature changes. Two costs per large view still grow with the sorting work, on the
server's loop (*measured* 2026-11-13, devcontainer, synthetic faces, `nice -n 19`, best
of 1, script in the session's scratchpad):

| Per large view (`FaceNames.tags`, `finding`) | today's size (22,000 faces, 18,336 named, 90 people) | 100,000 faces, 80,000 named |
|---|---:|---:|
| `Known.of(every, settings)`: `present` set, `follow_ids`, 18k-entry dicts, `np.stack` of every named vector | 46 ms | 266 ms |
| `likeness`: `np.stack` of **every** face's vector, then two matrix products | 34 ms | 122 ms |
| `np.stack` alone of every vector | 22 ms | 151 ms |

Both are recomputed from scratch at each call although their inputs (`faces.every`, the
`[people]` settings) are the very things `FaceIndex` and `people_memo` already keep.
A third cost grows with the number of **people**: `people_memo.signature_of` stats
`config.toml` + one file per person (91 stats today) at each large view — negligible on
Linux (*estimated* 2 ms), unknown under Docker Desktop's file sharing of a Windows
folder, where one `stat` may cost 1 ms or more (*to measure*: see *Needs maintainer*).
`FaceIndex.scanned()` also opens a new SQLite connection per call.

## Proposal

- `Known` kept with the key it was built under (the people memo's signature + the identity
  of `faces.every`): `Known.of` runs once per change of a name, not per large view.
- `FaceIndex.vectors`: the matrix of every vector, a `cached_property` beside `every`,
  dropped by `refresh()`; `likeness` and the people board take the matrix, not the rows.
- `people_memo`: one signature check per *grace* window (e.g. 1 s, a named constant: a
  change saved by the page itself invalidates at once since the page's own writer calls
  it; only an edit made by hand in an editor waits up to the grace). Decide the grace
  from the maintainer's `stat` measurement; without a measurement, keep the stat per call.
- A **test that pins the principle**: `tags()` on 1,000 named faces and on 80,000 named
  faces, after the first call, within the same order of time (a factor to state, e.g. < 3),
  so that a later change cannot make the large view grow with the sorting again.

## Acceptance

- [ ] The script of the table above rerun on the new code: `tags()` and `likeness()` after
      the first call under 5 ms at 100,000 faces / 80,000 named (*measured*, in the PR)
- [ ] `Known` and the matrix follow every change: a name given on the page, a face rejected,
      a `people --forget`, a photo moved by `sort` (`follow_ids`), a new face drawn (0715,
      `refresh()`), an edit of a people file by hand — one test per event
- [ ] The growth test above (1,000 vs 80,000 named faces) in `tests/unit/`
- [ ] The grace delay kept at zero (a stat per call) unless measured on the maintainer's PC (a step of `tests/measure/mh-measure.ps1` added for it), said in the status

## Where the user gains

Measured above: 80 ms of server work per large view today (120 ms per *who is on it* +
*their photos*), 390 ms once the library reaches 100,000 faces, both → under 5 ms
(*estimated*: a dictionary lookup and one matrix product). The large view's picture no
longer waits behind the names on the loop.
