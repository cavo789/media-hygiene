# 0627 — Ctrl+C while the pool's fork server starts prints a traceback, then an "unexpected error"

- **Priority**: Medium — no photo touched and the work done is kept, but a normal Ctrl+C shows a traceback and asks to report a bug; any command opening an image pool may be exposed (to check)
- **Batch**: interrupt
- **Depends**: —
- **Files**: `src/media_hygiene/services/runtime.py`, `src/media_hygiene/services/describing.py`, `src/media_hygiene/cli/tags_flow.py`, `src/media_hygiene/cli/meaning_flow.py`, `src/media_hygiene/cli/unexpected.py`, `tests/unit/test_cli_unexpected.py`, `tests/unit/test_interrupt.py`

## Problem

Seen by the maintainer on 2026-11-06 (image 0.4.0, PowerShell), `mh tags --meaning`:

1. a first Ctrl+C stops the meaning step ("Stopped: the next run of tags resumes…"), at 4,956 of 38,616 photos;
2. the command goes on with the next step: 14 photos to describe with the Ollama model;
3. a Ctrl+C just after that step starts prints a Python traceback ending inside `multiprocessing/forkserver.py`, line 235, `__import__(modname)`, while it preloads `scan.image_check` and numpy;
4. the command ends with `Unexpected error during tags: ExceptionGroup: unhandled errors in a TaskGroup (1 sub-exception)` and the invitation to report a bug.

The promises broken: Ctrl+C ends a command with one calm line, and the shipped image never shows a traceback.

## Likely cause (read in the code, not reproduced)

- The fork server is started when the first pool opens (`services/describing.py`, `with runtime.executor_factory()`). `tags` does not call `warm_pool`, so it starts at that moment and spends time importing numpy.
- Ctrl+C reaches every process of the terminal's group. `prepare_image_worker` protects the **workers** from SIGINT, not the fork server itself, which is still importing its preload list: it dies and writes the traceback to the terminal.
- To check: the sub-exception of the group, probably `BrokenProcessPool` as the pool loses its server. `-e MEDIA_HYGIENE_DEBUG=1` shows it. The stop was asked (`StopRequest`), yet this failure is treated as a bug.
- `stop_on_error` prints the group's generic message: even for a real bug, the report says nothing of what failed.

## What to do

1. **Reproduce** in a test or a script: send SIGINT to the process group during the fork server's preload. The window lasts a fraction of a second (0140 measured 0.58 s cold before 16 workers answer, on an earlier build), so a deliberately slow preload module may be needed.
2. **Protect the fork server from SIGINT** from its start, so that it survives until the parent closes the pool. To check: starting it with SIGINT ignored in the parent (`signal.signal` works only in the main thread, and `warm_pool` starts it from another thread; the disposition must also be restored at once), or another way of starting it in the background. Cover both `warm_pool` and a first start by `process_pool`.
3. **Stop asked + pool broken = a stop**: if the pool breaks after a stop was requested, end as Ctrl+C does, with what is done kept, not as an unexpected error.
4. **`stop_on_error` unwraps** an `ExceptionGroup` holding a single exception, to name the real error. A `KeyboardInterrupt` raised in a group must still end in `stop_on_interrupt`.
5. **Check the other pools**: audit, report, review, classify, people: the same Ctrl+C at their start.

## Decision of the maintainer (2026-11-06)

**One Ctrl+C stops the whole of `tags`**, with the resume line: a stop during `--meaning` no longer moves on to the description step, nor to the steps after it. This is to do in `tags_flow.run_tags`, along with items 1 to 5, which remain needed: the first Ctrl+C can still fall while a pool's fork server starts.

## Tests

- SIGINT during the preload: no traceback on stderr, the pool still answers (or ends as a stop).
- Pool broken after a stop request: exit code `INTERRUPTED`, no "Unexpected error" line.
- `stop_on_error` with a one-exception group names that exception; with several, stays readable.
- `tags --meaning`: a stop during the meaning step ends the command: no description step, no model called.

A change of console output: say whether `docs_screenshots` should run.
