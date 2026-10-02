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

## Status — PARTIAL (2026-10-02)

### Done
- Code read of the undo path (`services/undo.py`, `services/undo_guard.py`, `actions/undo.py`,
  `actions/reversal.py`, `actions/restore.py`, `actions/journal.py`, `actions/runs.py`):
  `undo` exits non-zero only on a `MediaHygieneError` (missing or read-only mounts, unknown
  run, corrupt journal, unknown action) or a crash; restore errors are reported with exit 0.
  Nothing depends on timing: run ids get a `-2`, `-3` suffix on collision, the refused `:ro`
  clean stops before creating a run, every journal line is fsync'ed, and each container of the
  test starts after the previous one exited (`docker wait`).
- About 170 runs of `pytest -m e2e -k audit_clean_undo` on the same image: one failure, and not
  in `undo`: the first `audit` exited **139** (SIGSEGV of the container's main process) with no
  output at all. A normal audit prints its "Audit" title within ~0.7 s, so the crash came
  before it: interpreter start, imports or `build_runtime` — code shared by every command. The
  2026-10-01 `undo` failure is most likely the same crash on another container (its output was
  not kept; unproven).
- `tests/support/docker.py::run_image` now starts every container with `PYTHONFAULTHANDLER=1`
  (Python and C stacks in the logs on a fatal signal) and, for an exit above 128, appends the
  container's `docker inspect .State` (OOMKilled, ExitCode, times). Checked on a deliberate
  segfault. The `e2e` helper keeps the pytest output in `/tmp/media-hygiene/e2e.log`.
- 30 consecutive capped runs (batches of 5) and one full e2e suite passed afterwards.

### Not done
- The root cause of the exit 139 (which library, or Docker/WSL itself) is unknown.
  **Reason:** one occurrence in ~170 runs, before the new diagnostics existed; the WSL VM
  restarted twice during the long loops, which also lost the kernel log of the crash. Next
  time it happens, read `/tmp/media-hygiene/e2e.log` (fault handler stack + container state)
  and `docker run --rm --privileged --user 0 --entrypoint dmesg media-hygiene:latest | grep
  -i segfault` before the VM restarts.
