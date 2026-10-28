# Working method — always apply

Lessons of real sessions (each one cost a rerun, a fix-up commit or a PARTIAL TODO). Methods:
`measure-before-ranking` skill; reviewer: `cache-invalidation-reviewer` agent.

- ✅ DO: before declaring done or committing, run the commit gate itself on what changed:
  `pre-commit run --config <the project's config> --files $(git status --porcelain | awk '{print $2}')`
  (here, the duplicate-code checks run at `git push` instead: stage `pre-push`; a refused
  push means a new file repeats another one — move the shared part to a helper).
  ❌ DON'T: trust a single-file `mypy`/`ruff` run: the gate's config differs (strict typing of
  tests, pylint's docstring and boolean checks). The `Stop` hook (`.claude/scripts/stop_gate.sh`)
  runs it on the changed files at the end of each turn and sends a failure back.
- ✅ DO: between two edits, run only the tests of what changed:
  `pytest $(python3 .claude/scripts/tests_for.py)` (the tests importing a changed module, in
  seconds); before declaring done, `--depth 1` (the tests of its importers too), then the
  commit gate. The whole suite is CI's job, or `check` when a change is cross-cutting (a
  `conftest.py`, a template, a constant every module reads). ❌ DON'T: run the whole suite after
  each edit (minutes of load on the maintainer's PC).
- ✅ DO: keep what passes to one line and what fails in full: `pytest -q --tb=short … | tail
  -25`, `pre-commit … | grep -v -e Passed -e Skipped`, `git push -q`. ❌ DON'T: cut a failure's
  trace to save room (guessing its cause costs more rounds than reading it).
- ✅ DO: before editing files near a size cap, `.claude/scripts/near_limit.sh <files>`; plan
  the split (a new module) before writing, not after the linter fails.
- ✅ DO: when a cache or index starts trusting more (reusing a listing, a stat, a digest), list
  every event that used to invalidate it — rename, move, atomic save (new inode), in-place
  write, copy keeping the mtime, `touch` — and keep one test per event.
- ✅ DO: for anything stored by path (index rows, settings files, decision files, caches),
  write what happens when the file moves: the tool's own moves (`sort`, `undo`, quarantine)
  and the user's (a folder renamed in Explorer). Test it.
- ✅ DO: when pairing files by content, break ties between identical copies (by name) and
  test with the demo tree's copies.
- ✅ DO: every figure in a TODO, commit message or summary says *measured* (how, where) or
  *estimated* (from what). ❌ DON'T: state a fact about a third-party product unchecked.
- ✅ DO: end a work session with **where the user gains**: before → after, in % when possible,
  measured or estimated — not only what changed.
- ✅ DO: a new limit or threshold a user with another machine or collection might want to
  change (sizes, counts, workers, days): say in the report whether it should be a setting.
- ✅ DO: before changing a design the user chose (mounts, data layout, a dependency), list
  what the change loses, and ask.

## Unattended runs (several TODOs in a row — `/todo:iterate`)

- A private feedback file `.claude/plans/feedback-<topic>.md`, kept as you go: per TODO the
  questions met, the choices and their alternatives, deviations from the TODO, what waits for
  the maintainer (measurements, decisions); at the end, the gains table.
- A work branch (`iterate/<date>`), one commit per lot pushed as it goes, `git fsck
  --no-dangling` first, never `git stash` (another session may share the tree), never `main`;
  a pull request at the end is the review (CI runs the heavy tests); the user merges.
- Notify the user (`PushNotification`) when the run ends or stops: they may be away.
- A TODO that needs the maintainer (a measurement on their machine, a decision, real files)
  is left for them, said in the feedback file, never guessed.

## media-hygiene — project specifics

- Devcontainer facts: no `pytest -n` here (xdist is installed for CI only: the PC suffers under load); a foreground `sleep` is refused (use a
  background run or a check loop); `ProcessPoolExecutor` in `python -c` needs the `fork`
  context; the scratchpad is invisible to the host Docker daemon (`docker cp`, or
  `-c "$(cat script.py)"`); heavy steps one at a time, `nice -n 19`, `PYTHON_CPU_COUNT=4`
  (the container itself is capped by `runArgs --cpus`, `MH_DEV_CPUS` on the host). Measuring:
  `/usr/bin/time -f '%e s %M KB'` (peak memory), `hyperfine` (repeated runs, spread),
  `py-spy record -o /tmp/x.svg -- <command>` (where the time goes); `jq`, `bc`, `file`, `unzip`.
- Measurements only the maintainer can run (Windows + Docker Desktop): add a step to
  `tests/measure/mh-measure.ps1` (PowerShell 5.1, ASCII) instead of a list of commands to type;
  its results file is read back from the devcontainer through a read-only mount of `C:\`.
  In it, never name a variable like a parameter in another case (`$photos` vs `-Photos`):
  PowerShell names ignore case, and a typed parameter (`[string]`) silently converts what
  is assigned (a list of files became one string, 2026-10-20).
- A change of console output or of a page makes the documentation captures stale: say that
  `docs_screenshots` should run; never run it unasked (image build + browser: heavy).
- The maintainer's reviews often turn a constant into a `config.toml` setting
  (`[cache] previews_max_gb`, `[classify] folder_town_ignore`): propose it in the feedback
  instead of waiting for the review.
- A page where photos are shown as tiles and picked (browse, search, phone, reviews): load the
  `photo-picking-pages` skill first — one layout, one way to pick, the same keys, from the shared
  `review/templates/pick_*` templates; a page that differs is a bug.
- Product rules the reviews keep checking: a save is proven by reading it back from disk and
  showing it (never "Saved" from memory); the shipped image never shows a traceback; the CLI
  teaches in one-liners (read-only 🔒, the undo line); documentation and captures are
  Windows-first, for Windows PowerShell 5.1; every command that needs a local AI model is
  flagged 🤖 where it is pasted.
