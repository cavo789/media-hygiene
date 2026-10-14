# 0159 — A first audit says how long it will take, and that the next ones take seconds

- **Priority**: Medium — a first audit of a large collection runs for tens of minutes to hours; nothing tells the user beforehand, nor that the work is kept and the next audit is fast
- **Batch**: guidance
- **Depends**: —
- **Files**: `src/media_hygiene/scan/broken.py`, `src/media_hygiene/scan/progress.py`, `src/media_hygiene/services/audit.py`, `src/media_hygiene/console/`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/start/01-first-audit.md`, `documentation/fr/start/01-first-audit.md`, `documentation/en/start/02-keep-the-cache.md`, `documentation/fr/start/02-keep-the-cache.md`, `tests/unit/`

## Context

Proposed on 2026-10-14 and accepted by the maintainer ("excellent retour pour l'utilisateur et
hyper rassurant sur la seconde exécution"). The pedagogy rule: users do not read the docs, the
tool reassures in one-liners.

Today a first audit shows its progress bars with an ETA once each pass has started, but:

- nothing says, before the long pass, how many files must be checked for the first time and
  roughly how long that takes (measured: ≈ 28 ms of CPU per 12 MP JPEG, ≈ 400 ms per HEIC;
  on a Windows folder through Docker the reading dominates, ≈ 460 MB/s at best);
- nothing says that stopping is safe (since 0143 the work is committed as it goes) and that
  the next audit takes seconds (a warm audit of 52,000 files: 3–4 s, measured);
- on a warm audit, nothing says that everything came from the cache.

## What to do

1. Before the integrity pass, when it has more than a threshold of files to check (e.g. 500),
   one line: "2,345 photos and 12 videos to check for the first time: about 20 min. You can
   stop at any time (Ctrl+C): what is checked is kept, and the next audit takes seconds."
   The estimate: time the first files of the pass (e.g. 30 s or 200 files), then print it once;
   or a per-kind default refined by the measured pace. Say "about", round generously.
2. At the end of a first audit, one line: what the next audit will cost ("Next audit: a few
   seconds, from the cache").
3. On a warm audit with nothing to check: "Nothing changed since the last audit: 52,056 files
   taken from the cache." (with the step line already shown in verbose mode).
4. Translations (fr) and docs en + fr (`start/01-first-audit.md`: what the first run costs and
   why; `start/02-keep-the-cache.md`: the second run). The captures of `start/01` change: say
   that `docs_screenshots` should run (heavy, the maintainer chooses when).

## Acceptance

- Unit tests: the line appears above the threshold with an estimate, not below; the warm line
  appears when nothing was checked; texts translated.
- The maintainer reads the lines on a first audit of the test folder of `mh-measure.ps1` and
  judges the estimate (within a factor of 2).

## Windows measurement (2026-10-14)

Measured by the maintainer on 2026-10-14 with `tests/measure/mh-measure.ps1` (Windows, Docker
Desktop, image built from `main`; runs `measures-20261014-2116` and `-2125`). First audit of 12,000 photos: "12,000 photos to check for the first time: less than a
minute" — the checks took 27.8 s, the audit 30 s; "Next audit: a few seconds" — the next audit
took 1.7 s. Within the factor of 2 of the acceptance. With 4,000 photos (checks 7.6 s) neither
line appears: they wait for `SAMPLE_SECONDS` (20 s) of checks, as designed.
