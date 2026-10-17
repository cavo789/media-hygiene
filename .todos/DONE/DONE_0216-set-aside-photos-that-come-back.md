# 0216 — Photos and videos you set aside that come back (a phone backup): recognised by content, proposed again

- **Priority**: Medium
- **Batch**: journal
- **Depends**: 0215
- **Files**: `src/media_hygiene/actions/kinds.py`, `src/media_hygiene/actions/remembered.py` (new), `src/media_hygiene/actions/journal.py`, `src/media_hygiene/actions/reversal.py`, `src/media_hygiene/scan/exact.py`, `src/media_hygiene/plan/returned.py` (new), `src/media_hygiene/plan/models.py`, `src/media_hygiene/services/audit.py`, `src/media_hygiene/services/clean.py`, `src/media_hygiene/cli/clean_confirm.py`, `src/media_hygiene/report/returned_views.py` (new), `src/media_hygiene/report/templates/_returned.html.j2` (new), `src/media_hygiene/report/templates/report.html.j2`, `src/media_hygiene/console/returned_view.py` (new), `src/media_hygiene/config/settings.py`, `src/media_hygiene/config/templates/config.toml.j2`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/unit/test_remembered.py` (new), `tests/integration/test_returned_files.py` (new), `documentation/en/clean/09-undo-history-purge.md`, `documentation/fr/clean/09-undo-history-purge.md`, `documentation/en/commands/clean.md`, `documentation/fr/commands/clean.md`

## Context

Asked by the maintainer on 2026-10-17: a user deletes every photo of someone (a former partner,
say), or photos and videos during a cleaning; months later, a phone is plugged in again for a
backup, the photos and videos are back, and the whole cleaning must be done again. "When I delete
something and the same photo or video comes back, whatever its name, it should be a candidate for
removal."

Everything needed is already kept: each set-aside is journaled with the file's SHA-256
(`actions/journaled.py`: `sha256` of every quarantine entry), and `purge` erases the quarantine of
a run, never its journal (`actions/purge.py`). `mh` mounts the journal folder for every command.

## What to do

- **What is remembered**: the files set aside by a choice without an identical copy kept — burst
  shots (`quarantine-burst`), near copies (`quarantine-near`), the photos chosen in `search`
  (0215's `quarantine-chosen`), the unwanted photos of 0206 (`quarantine-unwanted`, when it
  exists: whichever of 0206 and this TODO lands second adds it) — as a property of `ActionKind`,
  so that a new kind opts in. Not exact copies (their content is kept: a copy coming back is a
  plain duplicate), not broken or empty files.
- **The last word wins, per content (size, SHA-256)**: read from every journal; a later `undo`
  restoring the file forgets it (the user wanted it back). Measure the time to read the
  journals at each audit on a synthetic history (100,000 entries); if it is more than ~0.3 s,
  cache the set in the index, keyed by each journal file's name, size and mtime.
- **The audit**: the remembered sizes join the candidates of the exact pipeline (`scan/exact.py`:
  size, then partial, then full SHA-256), so a file of a remembered size is hashed and compared;
  a match is "back after being set aside", with the run that set it aside, its date and why. One
  line in *What you can do* ("23 photos you had set aside are back (45 MB): `clean` sets them
  aside again"), a report section with their previews.
- **`clean`, straightforward** (decided by the maintainer on 2026-10-17: "I already did the
  cleaning once, I do not want to start again: it must be straightforward"): the files that came
  back are part of `clean`'s plan by default, like the exact copies. Its usual question counts
  them on a line of their own ("↩️ 23 photos and videos you had already set aside are back
  (45 MB): back to the quarantine"); no other question, no option. Moved under a new kind
  `quarantine-returned` (remembered too). To keep one after all: `undo` of that clean; the last
  word is then the restore, and it is no longer proposed.
- **Clearly identified** before that: the audit's *What you can do* block says it on its own line
  with the next command (`mh clean`), the report shows them in a section of their own, each with
  its preview and when and why it was set aside, and `history` counts them apart.
- **A setting** `[clean] returned = true`: false never looks (no hashing of those sizes).
- **Size caps**: `actions/journal.py` (198/200), `plan/models.py` (197/200), `actions/reversal.py`
  (193/200), `services/audit.py` (182/200), `scan/exact.py` (179/200), `cli/clean_confirm.py`
  (178/200): the remembered set, the finding and the question live in new modules
  (`actions/remembered.py`, `plan/returned.py`, a console module); the existing files only call
  them.
- Without the journal mounted (a hand-written `docker run`): nothing is remembered; say it once in
  verbose.

## Explicit non-goals

- Deletions made outside the tool (Explorer): not remembered. From the index alone, a file gone
  looks the same as a file moved to a disk that is not plugged in; 0215 is the way to remove
  through the tool.
- A resized or recompressed version of a removed photo (different bytes): not recognised.
- New photos of the same person: a new photo is a new photo (no face rule).

## Acceptance

- Unit (`test_remembered.py`): the remembered set from journals — kinds in and out, an undo
  forgets, a later set-aside again remembers, a purged run still counts.
- Integration (`test_returned_files.py`): a burst shot set aside, its run purged, the same bytes
  copied back under another name and folder: the audit finds it with its first run and date; the
  next `clean` moves it back to the quarantine with the rest of its plan, counted on its own line;
  `undo` of that clean puts it back, and the audit after that no longer proposes it.
- Docs both languages: cleaning step 9 ("what you set aside stays set aside"), the `clean` page.
  Say in the report that `docs_screenshots` should run.
- Run the `cache-invalidation-reviewer` agent on the diff if the set is cached in the index.

## Gain (estimated)

A phone backup that brings back hundreds of photos removed months before: redoing the reviews and
the searches → one line in the audit and one answer to `clean`, whatever the files are now called.
