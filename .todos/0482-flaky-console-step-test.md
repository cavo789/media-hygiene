# 0482 — Flaky test: test_a_console_step_runs_while_the_server_stays_up

- **Priority**: High — it blocked the Docker Hub publish of main on 2026-10-29
- **Batch**: launcher
- **Depends**: —
- **Files**: `tests/unit/test_launcher_home.py`, `src/media_hygiene/cli/templates/mh.sh.j2`

## Why

CI of main (run 40896620300, merge of #56) failed once: got
`["home:relayed", "home:relayed", "ran:history", "status=0"]`-like lines (home relayed twice,
"At index 1 diff: 'home:relayed' != 'ran:history'"), while the same commit passed on the PR and
the file passes 6/6 in the devcontainer (measured). Likely a race in the fake home server of the
test (the step file read before `asks` is consumed), or 0480's change to the `watch.kept` relay.

## What

Find the race (run the test in a loop under CPU load: `stress` or `nice`/parallel copies),
fix the cause (test or script), never a retry.

## Acceptance

200 runs in a loop under load: 0 failure.
