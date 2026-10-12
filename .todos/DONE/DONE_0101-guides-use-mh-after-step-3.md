# 0101 — Guides 4–13 and sort 4–12: show `mh …` first, the long `docker run` folded

- **Priority**: Medium — two ways to do the same thing on every page
- **Batch**: docs
- **Depends**: —
- **Files**: `documentation/en/clean/*.md`, `documentation/fr/clean/*.md`, `documentation/en/sort/*.md`, `documentation/fr/sort/*.md`, `tests/support/docs/scenario.py`

## Context

UX review of 2026-10-12. Step 3 ends by introducing `mh` ("write your folders once"), and both
quick guides use it everywhere. But the step-by-step pages after step 3 never do: `grep -c "mh "`
gives 0 on every page of `clean/04…13` and `sort/04…12` except `09-undo-history-purge` and
`10-sort-by-person`, while they hold 1 to 5 full `docker run` blocks each (eight lines, seven
`-v`). A beginner who just created `mh` wonders whether to use it or to paste the long block,
and whether the long one mounts something `mh` does not.

## Goal

- On every step page after step 3, the command is shown first as `mh …` (what the reader types),
  followed by a `<details>` *Without `mh`: the full command*, as the quick guides already do.
- The explanation of a new part (`-p 127.0.0.1:8088:8088`, `/journal`…) stays, worded as
  "`mh` adds it for you; in the full command it is …".
- Both languages; `docs_screenshots` captures are unchanged (outputs, not commands).

## Acceptance

- Every step page from 4 on shows `mh` first; `test_documentation` passes.
