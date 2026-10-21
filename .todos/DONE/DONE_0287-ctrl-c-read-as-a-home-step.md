# 0287 — Ctrl+C on a page opened from home must end the loop, not run step 30

- **Priority**: high
- **Batch**: unassigned
- **Depends**: —
- **Files**: src/media_hygiene/cli/templates/mh_menu.ps1.j2, src/media_hygiene/cli/templates/mh.sh.j2, src/media_hygiene/review/home_views.py (`STEP_EXIT_BASE`), src/media_hygiene/constants.py (`ExitCode.INTERRUPTED`), tests/unit/test_launcher_home.py

## Context

The loop of `mh` alone (`_mh_home`, `mh_menu.ps1.j2:15-61`; the bash twin in `mh.sh.j2:142-190`)
reads any exit code above `STEP_EXIT_BASE` (100) as "step `code − 100` chosen on the page".
Ctrl+C ends the container with `ExitCode.INTERRUPTED` = 130, so it is read as **step 30**:

- when step 30 is not in `mh menu`'s list and a step already ran (`$after`), the loop opens the
  home page again: the maintainer had to press Ctrl+C twice after the burst review (2026-10-21);
- when step 30 is listed, it **runs**: on the demo tree, `hygiene --color never menu` lists
  `30	people --forget` (measured 2026-10-21, devcontainer). Any page opened from home, or home
  itself, can then launch an unrelated step on Ctrl+C.

The script's own comment says "Quit, Ctrl+C or an error end the loop": the intent is clear.

## Acceptance

- [ ] Only codes in `STEP_EXIT_BASE + 1 … STEP_EXIT_BASE + <max steps>` are read as steps; the
      step range must never reach 128+ (signals): a guard (constant or test) says so, e.g.
      steps capped below 28, or the base moved / the interrupt code checked first.
- [ ] Ctrl+C (130), and any other signal code (128 + n), ends the loop in PowerShell and in bash,
      prompt back, home not reopened, exit code kept.
- [ ] Tests in `test_launcher_home.py` (both shells): 130 after a step, 130 from home alone,
      a real step code still runs its step.
- [ ] The documentation's "launcher" page still matches (en + fr) if it describes Ctrl+C.
