# 0053 — e2e: `undo` after `clean` exited non-zero once in four runs

- **Priority**: Medium — an intermittent failure of the undo path, seen in the real image
- **Batch**: docker
- **Depends**: —
- **Files**: `tests/e2e/test_docker_image.py`, `src/media_hygiene/services/undo.py`, `src/media_hygiene/services/undo_guard.py`

## Context

While processing TODO 0029 (2026-10-01), `uv run pytest -m e2e` failed once in
`test_audit_clean_undo_cycle` at `assert undo.startswith("0\n"), undo` (line 63): the `undo`
run inside the container returned a non-zero exit code. The same suite then passed three times
in a row with the same image, and the test passed when run alone. TODO 0029 does not touch
`clean` nor `undo`; the failure output (the `undo` console text) was not kept.

Possible causes, none checked: a timing issue between the `clean` run and the `undo` guard
added by 0052 (journal or quarantine state read too early), a run-id collision when two runs
start within the same second (`YYYYMMDD-HHMMSS` ids), or a Docker volume not yet flushed.

## Proposal

- Run the e2e suite in a loop (e.g. 20 times) to reproduce; print the `undo` output on failure
  (it is already in the assertion message: keep the pytest output).
- If run ids collide within one second, make them unique (or make `undo` pick the right run).

## Acceptance

- [ ] Cause found and fixed, or the flake shown to be in the test harness and fixed there.
- [ ] 20 consecutive e2e runs pass.
