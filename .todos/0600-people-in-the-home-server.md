# 0600 — `people` served by the home server once the faces are found

- **Priority**: Low
- **Batch**: one-interface
- **Depends**: 0594 (DONE)
- **Files**: `src/media_hygiene/cli/people_flow.py`, `src/media_hygiene/services/people_page.py`, `src/media_hygiene/review/step_watch.py`

## Why (study of 0594)

`people` first looks for the faces the cache lacks, with a progress bar in the window, for hours on
a first run; only then does it serve its page. With nothing left to find, nothing keeps it apart.

## What

A `/people/` prefix when no face is missing; else today's path. The finding itself as a step of the
page is 0586's kind of work.

## Done when

With every face found, the step changes page without ending the server (test); with faces missing,
it runs as today.
